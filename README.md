# Dzcoin_bot : mise en route

1. Dans @BotFather : /mybots → Dzcoin_bot → Bot Settings → Menu Button (facultatif).
2. Héberge ce dossier sur un service qui donne une adresse **HTTPS** (Render, Railway, etc.).
3. Variables d'environnement :
   - BOT_TOKEN = le token de BotFather (secret !)
   - WEBAPP_URL = l'adresse HTTPS de ton serveur
4. Commandes : `pip install -r requirements.txt`
   - serveur : `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - bot : `python bot.py`
5. Pubs : inscris-toi sur Adsgram, crée un bloc « Rewarded », puis mets son identifiant dans static/index.html (ADSGRAM_BLOCK_ID).
