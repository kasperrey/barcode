import pickle

gegevens = {"5059937252889": [13, "NOORDZEEvis"], "7622210100092": [3, "Bil-Bilbos"], "32149869": [0.50, "gehaktworst"], "5412971016853": [6.50, "Crak's"],
	"8712285353086": [20, "Fromage De La France"], "4550456643680": [7.75, "aardbeienconfituur CLEYSSENS"], "4550455678980": [5, "ananas Mr. CHAT"], "32149869": [2.95, "cappelinni"], "0737872948696": [3.30, "wasdoekjes HEMA"], "5400210535388": [1.50, "tandeborstel Axé"]}

pickle.dump(gegevens, open('data', 'wb'))
