import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers, models


# Charger dataset (exemple CSV pré-traité)
df_train = pd.read_csv("Data/archive/mitbih_train.csv", header=None)
df_test  = pd.read_csv("Data/archive/mitbih_test.csv", header=None)

X_train = df_train.iloc[:, :-1].values
y_train = df_train.iloc[:, -1].values
X_test = df_test.iloc[:, :-1].values
y_test  = df_test.iloc[:, -1].values

# Normalisation
X_train = (X_train - X_train.mean()) / X_train.std()
X_test  = (X_test - X_test.mean()) / X_test.std()

X_train = X_train.reshape(-1, 187, 1)
X_test = X_test.reshape(-1, 187, 1)

y_train = keras.utils.to_categorical(y_train, 5)
y_test  = keras.utils.to_categorical(y_test, 5)

# Créer modèle CNN
model = models.Sequential([
    layers.Conv1D(32, 5, activation='relu', input_shape=(187,1)),
    layers.MaxPool1D(2),
    layers.Conv1D(64, 5, activation='relu'),
    layers.GlobalAveragePooling1D(),
    layers.Dense(32, activation='relu'),
    layers.Dense(5, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Entraînement
model.fit(X_train, y_train, epochs=10, batch_size=128, validation_split=0.1)

# Évaluation
loss, acc = model.evaluate(X_test, y_test)
print("Accuracy:", acc)

# Sauvegarder modèle pour Fog
model.save("models/ecg_cnn.h5")
