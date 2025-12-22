# Agents IA (chatbot pour MS Teams)

Suite d'assistants IA connectés a MS Teams

## Objectif

Ouvrir une porte d'accès aux modèles d'IA pour les équipes d'elmy.

L'objectif du projet est de:

- Exposer les diferents modèles (GPT4, Gemini, et autres) via teams.
- Controler et réduire les coups et usages des modèles IA.

## Install & Deployment

### dev setup

Ce projet est developpé en python3.10+. La gestion des
dépendances est faite via `uv`.

```bash
# Installer uv via curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Installer les dépendances

```bash
uv lock
uv sync
```

#### Configurer les variables d'environnement

Copier le fichier `.env.example` en `.env` et remplir les variables d'environnement.

```bash
> uv run -m elmybots
 __  __    __    ____  ____  _  _   
(  \/  )  /__\  (  _ \(_  _)( \/ )  
 )    (  /(__)\  )   /  )(   \  /   
(_/\/\_)(__)(__)(_)\_) (__)  (__)   
   ____  _  _    ____  __    __  __  _  _ 
  (  _ \( \/ )  ( ___)(  )  (  \/  )( \/ )
   ) _ < \  /    )__)  )(__  )    (  \  / 
  (____/ (__)   (____)(____)(_/\/\_) (__) 

2025-09-11 15:06:01,412 ℹ️  __main__: Starting chatbot MARTY (port: 3978)
```

#### 🐳 docker

Pour uniquement tester en local, vous pouvez utiliser docker pour construire et exécuter l'image.

```bash
docker build -t chatbot .
docker run -it -p 3978:3978 chatbot
```

### ⚠️ NGROK & routing

Pour tester le bot, vous devez exposer le serveur local, pour ceci vous pouvez utiliser ngrok.

```bash
ngrok http 3978 --host-header="0.0.0.0:(PORT)"

ngrok                                                                                                           (Ctrl+C to quit)
                                                                                                                                
K8s Gateway API https://ngrok.com/early-access/kubernetes-gateway-api                                                           
                                                                                                                                
Session Status                online                                                                                            
Account                       Adrian Toledano (Plan: Free)                                                                      
Update                        update available (version 3.8.0, Ctrl-U to update)                                                
Version                       3.3.2                                                                                             
Region                        Europe (eu)                                                                                       
Latency                       83ms                                                                                              
Web Interface                 http://127.0.0.1:4040                                                                             
Forwarding                    https://956e-80-103-137-137.ngrok-free.app -> http://localhost:3978                               
                                                                                                                                
Connections                   ttl     opn     rt1     rt5     p50     p90                                                       
                              70      0       0.00    0.00    80.68   134.59                                                    
                                                                                                                                
HTTP Requests                                
```

Dans cette execution, on copie l'endpoint de ngrok ; dans l'exemple: `https://956e-80-103-137-137.ngrok-free.app`


---

## Configurer le bot coté Azure

- `Create a Resource` - `Azure Bot`

 
![Alt text](docs/images/createazure.png)

Ici, attention à

- pricing tiers = free !
- type of app: multitenant


Si tout va bien

![Alt text](docs/images/azure_deployment_bot_ok.png)

## Configurer le bot

![Alt text](docs/images/azure_config_bot.png)

Inserez l'endpoint de ngrok dans le champ `Messaging endpoint`
avec le path `/api/messages`. e.g.
`https://956e-80-103-137-137.ngrok-free.app/api/messages`


Si les variables d'environnement sont correctes (voir `.env`), le bot devrait être en ligne, et vous pouvez le tester
directement sur `Test in Web Chat`

![Alt text](docs/images/azure_test_webchat.png)

## Créer une APP teams

Go sur `/teams-app/manifest.json`.

Remplazer les champs `botId` avec le AppId.

Ensuite, il faut zipper les trois fichiers dans un fichier `app.zip`.

![Alt text](docs/images/teams_upload_app.png)

## Deployment

Follow elmy headlines for deployment.
