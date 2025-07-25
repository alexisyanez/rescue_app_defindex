# Rescue Bot and Alert Managment

This project is an integration between rescue-bot app from:  bot for DeFindex. Below are the steps to initialize and configure the project correctly.

## Prerequisites
- Look at https://github.com/alexisyanez/defindex/tree/app/rescue-bot/apps/rescue_bot README.md
- Python (v3.x+) 

## Configuration

- Set all the credential in the `.env` file
- Fill up all the neccesary key in the file `mainnet.contracts.json` 
- Set your network properly in the `soroban-toolkit.ts` line 8:
```
network: 'mainnet'
```

## Running

- Run the python script `main.py` to launch the bot "bot_alert_rescue"
