from gophish import Gophish
from gophish.models import *
import requests
import urllib3
import os

urllib3.disable_warnings()

# Get Gophish API key
api_key = input("Please enter the API key of your Gophish:")
api = Gophish(api_key, verify=False)

# Function to check if an SMTP profile exists
def does_smtp_profile_exist():
    smtp_profiles = api.smtp.get()
    return any(profile.name == "Gophish sending profile" for profile in smtp_profiles)

# Create SMTP profile if it doesn't exist
if not does_smtp_profile_exist():
    smtp = SMTP(name="Gophish sending profile", host="mailcatcher:1025",
                from_address="johndoe@example.com", interface_type="SMTP",
                ignore_cert_errors=True)
    api.smtp.post(smtp)

# Function to check if a campaign exists
def does_campaign_exist(campaign_name):
    campaigns = api.campaigns.get()
    return any(campaign.name == campaign_name for campaign in campaigns)

def does_template_exist(template_name):
    templates = api.templates.get()
    return any(template.name == template_name for template in templates)

def does_landingpage_exist(landingpage_name):
    pages = api.pages.get()
    return any(page.name == landingpage_name for page in pages)

def does_group_exist(group_name):
    groups = api.groups.get()
    return any(group.name == group_name for group in groups)

def is_url_reachable(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code < 400  # Check if the status code is in the success range
    except requests.ConnectionError:
        return False

# Collect data for multiple campaigns
campaigns = []
campaign_count = int(input("How many campaigns do you want to create?"))
for campaign_index in range(campaign_count):
    campaign_name = input(f'Campaign {campaign_index + 1}: What is the name of your campaign? ')
    while True:
        # Get the template name from the user
        template_name = input(f'Campaign {campaign_index + 1}: What is the name of your template file inside the "email-templates" folder? ')
        template_filename = f'email-templates/{template_name}'
        if os.path.exists(template_filename):
            with open(template_filename, 'r') as file:
                template_content = file.read()
            break  # Exit the loop if the file exists
        else:
            print(f'The file "{template_filename}" does not exist. Please enter a valid template name.')

    landing_page_name = input('What is the name of the landing page? ')
    while True:
        landing_page_url = input('What is the URL of the site to be imported? ')
        # Check if the entered URL is reachable
        if is_url_reachable(landing_page_url):
            break
        else:
            print("Error: The entered URL is not reachable. Please try again.")
    while True:
        redirect_url = input('Where should the user be redirected? ')
        # Check if the entered URL is reachable
        if is_url_reachable(redirect_url):
            break
        else:
            print("Error: The entered URL is not reachable. Please try again.")
    group_name = input('How should the receiving group be called? ')
    group = input('Who should receive the mail (e.g. Alice Tyler <alice@doe.com>, Bob Martin <bob@doe.com>): ')

    # Create campaign data dictionary
    campaign_data = {
        "name": campaign_name,
        "template_name": template_name,
        "landing_page_name": landing_page_name,
        "landing_page_url": landing_page_url,
        "redirect_url": redirect_url,
        "group_name": group_name,
        "group": [item.strip() for item in group.split(',')]
    }

    campaigns.append(campaign_data)

# Loop through campaigns and create necessary entities
for campaign in campaigns:
    print(campaign)
    if not does_campaign_exist(campaign['name']):
        print("Creating campaign...")

        # Create landing page
        fetched_url = requests.get(campaign['landing_page_url'])
        page = Page(name=campaign['landing_page_name'], html=fetched_url.text,
                    capture_credentials=True, capture_passwords=True,
                    redirect_url=campaign['redirect_url'])
        page = api.pages.post(page)
        print("Landing Page created")

        template = Template(name=campaign["template_name"], html=template_content)
        template = api.templates.post(template)
        print("Email template created")

        # Create user & group
        targets = []
        for item in campaign['group']:
            # Split the item into name and email
            name, email = item.split('<')

            # Extract first and last names
            first_name, last_name = name.strip().split() if ' ' in name else ('', '')

            # Create a User object and append it to the targets list
            user = User(first_name=first_name, last_name=last_name, email=email.rstrip('>').strip())
            targets.append(user)
        group = Group(name=campaign["group_name"], targets=targets)
        group = api.groups.post(group)
        print("Users & Group created")

        # Create campaign
        groups = [Group(name=campaign["group_name"])]
        page = Page(name=campaign['landing_page_name'])
        template = Template(name=campaign["template_name"])
        smtp = SMTP(name="Gophish sending profile")
        url = 'http://phishing_server'
        campaign_entity = Campaign(name=campaign["name"], groups=groups, page=page,
                                   template=template, smtp=smtp)
        campaign_entity = api.campaigns.post(campaign_entity)
