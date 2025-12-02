#!/usr/bin/env python3
# train_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import pickle

def main():
    print("[*] Cargando dataset...")
    try:
        df = pd.read_csv('features.csv')
    except FileNotFoundError:
        print("[!] features.csv no encontrado. Ejecuta extract_features.py primero.")
        return

    # Features para entrenamiento
    feature_cols = ['max_entropy', 'suspicious_headers', 'total_header_len', 'ratio']
    X = df[feature_cols]
    
    # En un escenario real, entrenaríamos solo con tráfico normal.
    # Aquí usamos Isolation Forest que es no supervisado (detecta outliers).
    
    print("[*] Entrenando modelo Isolation Forest...")
    # contamination=0.1 asume que el 10% de los datos son anomalías
    clf = IsolationForest(random_state=42, contamination=0.2)
    clf.fit(X)
    
    # Predicción (-1 = anomalía, 1 = normal)
    y_pred = clf.predict(X)
    
    # Convertir a 0 (normal) y 1 (anomalía) para comparar con nuestra etiqueta manual
    y_pred_binary = [1 if x == -1 else 0 for x in y_pred]
    
    # Nuestra etiqueta manual 'is_malicious' (solo para validar)
    y_true = df['is_malicious']
    
    print("\n" + "="*40)
    print("RESULTADOS DE DETECCIÓN")
    print("="*40)
    print(classification_report(y_true, y_pred_binary, target_names=['Normal', 'Malicioso']))
    
    print("\nMatriz de Confusión:")
    print(confusion_matrix(y_true, y_pred_binary))
    
    # Guardar modelo
    with open('model.pkl', 'wb') as f:
        pickle.dump(clf, f)
    print("\n[✓] Modelo guardado en model.pkl")

if __name__ == '__main__':
    main()
