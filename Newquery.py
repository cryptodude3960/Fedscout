import requests
import os
import json
from datetime import datetime, timedelta
import time

class FederalContractingClient:
    def __init__(self, client_name):
        self.client_name = client_name
        self.client_data = {
            "registration_status": "Unknown",
            "capability_statement": "Not Reviewed",
            "past_performance": [],
            "compliance": "Unknown",
            "current_opportunities": [],
            "next_steps": []
        }
    
    def update_status(self, key, value):
        if key in self.client_data:
            self.client_data[key] = value
        else:
            print(f"Invalid key: {key}")
    
    def add_past_performance(self, contract_details):
        self.client_data["past_performance"].append(contract_details)
    
    def add_opportunity(self, opportunity_details):
        self.client_data["current_opportunities"].append(opportunity_details)
    
    def add_next_step(self, step):
        self.client_data["next_steps"].append(step)
    
    def display_summary(self):
        print(f"\nFederal Contracting Summary for {self.client_name}")
        for key, value in self.client_data.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

class FederalContractingTool:
    def __init__(self, storage_file="contracting_clients.json"):
        self.clients = {}
        self.api_key = os.getenv("SAM_GOV_API_KEY", "yfztBk00vlrpghK7wf84zDGKUnNtPPfiB3IgvFU6")
        self.storage_file = storage_file
        self.load_clients()
    
    def add_client(self, client_name):
        if client_name not in self.clients:
            self.clients[client_name] = FederalContractingClient(client_name)
            self.save_clients()
        else:
            print(f"Client {client_name} already exists.")
    
    def get_client(self, client_name):
        return self.clients.get(client_name, None)
    
    def list_clients(self):
        return list(self.clients.keys())
    
    def display_all_clients(self):
        for client_name in self.clients:
            self.clients[client_name].display_summary()
    
    def save_clients(self):
        with open(self.storage_file, "w") as f:
            json.dump({name: client.client_data for name, client in self.clients.items()}, f, indent=4)
    
    def load_clients(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r") as f:
                data = json.load(f)
                for name, client_data in data.items():
                    client = FederalContractingClient(name)
                    client.client_data = client_data
                    self.clients[name] = client
    
    def fetch_sam_gov_opportunities(self, naics_codes, start_date, end_date):
        base_url = "https://api.sam.gov/prod/opportunities/v2/search"
        headers = {"Accept": "application/json"}
        
        all_opportunities = []
        start_date_obj = datetime.strptime(start_date, "%m/%d/%Y")
        end_date_obj = datetime.strptime(end_date, "%m/%d/%Y")
        
        while start_date_obj < end_date_obj:
            next_end_date_obj = min(start_date_obj + timedelta(days=365), end_date_obj)
            params = {
                "api_key": self.api_key,
                "limit": 10,
                "postedFrom": start_date_obj.strftime("%m/%d/%Y"),
                "postedTo": next_end_date_obj.strftime("%m/%d/%Y")
            }
            
            for naics_code in naics_codes:
                params["filters"] = f"naicsCode:{naics_code}"
                try:
                    response = requests.get(base_url, params=params, headers=headers)
                    
                    if response.status_code == 429:
                        print("Rate limit exceeded. Waiting before retrying...")
                        time.sleep(10)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    opportunities = data.get("opportunitiesData", [])
                    
                    if opportunities:
                        all_opportunities.extend(opportunities)
                    else:
                        print(f"No current opportunities found for NAICS {naics_code} in range {params['postedFrom']} to {params['postedTo']}")
                
                except requests.exceptions.HTTPError as http_err:
                    print(f"HTTP error: {http_err} - {response.text}")
                except requests.exceptions.RequestException as req_err:
                    print(f"Request error: {req_err}")
                except Exception as e:
                    print(f"Unexpected error: {e}")
            
            start_date_obj = next_end_date_obj + timedelta(days=1)
        
        return all_opportunities
    
    def update_client_opportunities(self, client_name, naics_codes, start_date, end_date):
        client = self.get_client(client_name)
        if client:
            opportunities = self.fetch_sam_gov_opportunities(naics_codes, start_date, end_date)
            for opportunity in opportunities:
                client.add_opportunity(opportunity.get("title", "No Title Available"))
            self.save_clients()
        else:
            print(f"Client {client_name} not found.")

# Example Usage
if __name__ == "__main__":
    tool = FederalContractingTool()
    tool.add_client("Crown Jewels Produce")
    client = tool.get_client("Crown Jewels Produce")
    
    if client:
        client.update_status("registration_status", "SAM.gov Registered")
        client.update_status("capability_statement", "Needs Improvement")
        client.add_past_performance("DLA Troop Support - Fresh Produce Supply Contract")
        
        # User-specified date range and NAICS codes
        start_date = "01/01/2024"
        end_date = "03/17/2025"
        naics_codes = ["424480", "311991"]
        
        tool.update_client_opportunities("Crown Jewels Produce", naics_codes, start_date, end_date)
        client.add_next_step("Finalize Capability Statement with Past Performance Details")
        client.display_summary()

    tool.add_client("ABC Logistics")
    print("\nAll Clients:", tool.list_clients())
    tool.display_all_clients()
