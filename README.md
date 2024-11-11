# polar_cardio

 ![Supported Python Versions](https://img.shields.io/badge/Python-3.11-blue.svg?logo=python&logoColor=white)

```
git clone https://github.com/Gab1i/polar_cardio.git

cd polar_cardio

pip install -r requirements.txt

```

## vérifier l'adresse de la ceinture cardiaque
```
python list_devices.py

```

Le code affiche la liste des appareils bluetooth disponibles à portée du PC. Il faut récupérer l'adresse associée à la ceinture Polar H10 correspondante.

Sous MacOS, l'adresse est au format UUID. ex: **FADD5FC9-7432-21BA-7D18-0A984CCF13BD**

Sous Windows, l'adresse est une adresse MAC. ex: **FC:40:BC:A4:D5:63**

## Ajouter l'adresse dans la liste du programme principal
Dans le fichier __main.py__, ligne 239, le dictionnaire __list_polar__ permet d'ajouter/modifier des adresses au format "nom_du_device": "adresse".

## Lancer le programme
```
python main.py

```

Au lancement, 
- Entrer le numéro d'anonymat puis appuyer sur Entrée.
- Entrer le numéro correspondant à la ceinture à utiliser puis appuyer sur Entrée

Pour quitter, appuyer sur n'importe quelle touche.

## Récupérer les données
Les données brutes sont automatiquement enregistrées dans le dossier **rawdata**
