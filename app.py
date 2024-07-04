import base64
import io
import os

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file
from sklearn.metrics import mean_squared_error, r2_score

from map import add_new_point, create_map
from utils import get_combined_forest

app = Flask(__name__)

scaler = joblib.load('models/scaler.joblib')
best_model_linear_regression = joblib.load('models/model_linear_regression.joblib')
best_model_random_forest = get_combined_forest()
best_model_svr = joblib.load('models/model_svr.joblib')

df_new = pd.read_csv('csv/weatherWithCoordsImputed.csv')
df_new['Date'] = pd.to_datetime(df_new['Date']).map(pd.Timestamp.toordinal)

X_transformed_new = scaler.transform(df_new[['Date', 'Latitud', 'Longitud']])

y_pred_new_linear_regression_name = 'models/y_pred_new_linear_regression.joblib'
if not os.path.exists(y_pred_new_linear_regression_name):
    y_pred_new_linear_regression = best_model_linear_regression.predict(X_transformed_new)
    joblib.dump(y_pred_new_linear_regression, y_pred_new_linear_regression_name)
else:
    y_pred_new_linear_regression = joblib.load(y_pred_new_linear_regression_name)

y_pred_new_random_forest_name = 'models/y_pred_new_random_forest.joblib'
if not os.path.exists(y_pred_new_random_forest_name):
    y_pred_new_random_forest = best_model_random_forest.predict(X_transformed_new)
    joblib.dump(y_pred_new_random_forest, y_pred_new_random_forest_name)
else:
    y_pred_new_random_forest = joblib.load(y_pred_new_random_forest_name)

y_pred_new_svr_name = 'models/y_pred_new_svr.joblib'
if not os.path.exists(y_pred_new_svr_name):
    y_pred_new_svr = best_model_svr.predict(X_transformed_new)
    joblib.dump(y_pred_new_svr, y_pred_new_svr_name)
else:
    y_pred_new_svr = joblib.load(y_pred_new_svr_name)

df_new['predicted_max_temp_linear_regression'] = y_pred_new_linear_regression
df_new['predicted_max_temp_random_forest'] = y_pred_new_random_forest
df_new['predicted_max_temp_svr'] = y_pred_new_svr


def create_plot1():
    importances = best_model_random_forest.feature_importances_
    columns = ['Date', 'Latitud', 'Longitud']
    feature_importances_df = pd.DataFrame({
        'feature': columns,
        'importance': importances
    }).sort_values('importance', ascending=False)
    plt.figure()
    plt.bar(feature_importances_df['feature'], feature_importances_df['importance'])
    plt.xlabel('Características')
    plt.ylabel('Importancia')
    plt.title('Importancia de las Características')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img


def create_plot2():
    plt.figure()
    scatter = plt.scatter(df_new['Longitud'], df_new['Latitud'], c=df_new['MaxTemp'], cmap='viridis')
    plt.xlabel('Longitud')
    plt.ylabel('Latitud')
    plt.colorbar(scatter, label='Temperatura Máxima')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img


def create_prediction_plot(model_name, y_test, y_pred):
    plt.figure()
    plt.scatter(y_test, y_pred, alpha=0.5)
    plt.xlabel('Real')
    plt.ylabel('Predicho')
    plt.title(f'{model_name}\nError Cuadrático Medio: {mean_squared_error(y_test, y_pred):.2f}\nCoeficiente de Determinación R²: {r2_score(y_test, y_pred):.2f}')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img


@app.route('/')
def index():
    plot1 = create_plot1()
    plot2 = create_plot2()
    plot_linear_regression = create_prediction_plot('Linear Regression', df_new['MaxTemp'], df_new['predicted_max_temp_linear_regression'])
    plot_random_forest = create_prediction_plot('Random Forest', df_new['MaxTemp'], df_new['predicted_max_temp_random_forest'])
    plot_svr = create_prediction_plot('Support Vector Machines', df_new['MaxTemp'], df_new['predicted_max_temp_svr'])
    return render_template('index.html', plot1=plot1, plot2=plot2, plot_linear_regression=plot_linear_regression,
                           plot_random_forest=plot_random_forest, plot_svr=plot_svr)


@app.route('/predict', methods=['POST'])
def predict():
    datos = request.json
    df_new = pd.DataFrame([datos])
    df_new['Date'] = pd.to_datetime(df_new['Date'], dayfirst=True).map(pd.Timestamp.toordinal)
    X_transformed_new = scaler.transform(df_new[['Date', 'Latitud', 'Longitud']])
    y_pred_new_linear_regression = best_model_linear_regression.predict(X_transformed_new)
    y_pred_new_random_forest = best_model_random_forest.predict(X_transformed_new)
    y_pred_new_svr = best_model_svr.predict(X_transformed_new)
    df_new['predicted_max_temp_linear_regression'] = y_pred_new_linear_regression
    df_new['predicted_max_temp_random_forest'] = y_pred_new_random_forest
    df_new['predicted_max_temp_svr'] = y_pred_new_svr
    df_new['Date'] = pd.to_datetime(df_new['Date'].map(pd.Timestamp.fromordinal)).dt.strftime('%d-%m-%Y')
    df_new['predicted_max_temp_linear_regression'] = df_new['predicted_max_temp_linear_regression'].round(1)
    df_new['predicted_max_temp_random_forest'] = df_new['predicted_max_temp_random_forest'].round(1)
    df_new['predicted_max_temp_svr'] = df_new['predicted_max_temp_svr'].round(1)
    df_dict = df_new.iloc[0].to_dict()

    add_new_point(datos.get('Nombre', 'point'), df_dict['Latitud'], df_dict['Longitud'], df_dict['predicted_max_temp_random_forest'])
    create_map()

    return jsonify(df_dict)


@app.route('/map')
def show_map():
    return send_file('templates/map.html')


if __name__ == '__main__':
    app.run(debug=True)
