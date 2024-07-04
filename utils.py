import io

import joblib


def get_combined_forest():
    part1_path = 'models/model_random_forest_part1.joblib'
    part2_path = 'models/model_random_forest_part2.joblib'

    # Leer las partes desde los archivos separados
    with open(part1_path, 'rb') as f:
        part1 = f.read()
    with open(part2_path, 'rb') as f:
        part2 = f.read()

    # Juntar las partes en memoria
    combined_content = part1 + part2

    # Cargar el modelo desde el contenido combinado en memoria
    combined_io = io.BytesIO(combined_content)
    model = joblib.load(combined_io)

    return model
