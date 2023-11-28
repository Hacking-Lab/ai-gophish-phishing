import requests
import argparse
import os

ai_proxy = "http://127.0.0.1:3000/endpoint"

def handle_arguments():
    parser = argparse.ArgumentParser(description=
                                     """
                                     The following script helps to create Email Templates with the AI,
                                     to create Phishing content.
                                     """)
    parser.add_argument("proxy", help="Proxy to communicate with OpenAI-API")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = handle_arguments()
    # Create email template
    while True:
        template_filename = input('Whats the name of the template (no whitespaces) ? ')
        template_systemcontent = input('What is the system content of the AI. e.g You are a helpful assistant.: ')
        template_prompt = input('What should be the context of the email template? Please be specific.: ')
        prompt = {
            'promptText': [template_prompt],
            'systemContent': [template_systemcontent]
            }
        print("Proccessing your request...")
        template_ai = requests.post(args.proxy, headers={'Content-Type': 'application/json'}, json=prompt, verify=False)
        template_filename = f'email-templates/{template_filename}.html'

        # Check if the file already exists
        if os.path.exists(template_filename):
            user_input = input(
                f"The file '{template_filename}' already exists. Do you want to override it? (Press Enter for Yes, or type 'N' for No): ")
            if user_input.lower() != 'n':
                # If the user wants to override or pressed Enter, open the file in write mode ('w')
                with open(template_filename, 'w') as template_file:
                    template_file.write(template_ai.text)
                print(f"File '{template_filename}' has been overridden.")
            else:
                print("File override canceled. No changes were made.")
        else:
            # If the file does not exist, create a new file
            with open(template_filename, 'w') as template_file:
                template_file.write(template_ai.text)
            print(f"File '{template_filename}' has been created.")
            print("Please check the created file.")
        done_loop = input("Enter 'r' to regenerate the email or Press Enter to end the script.")
        if done_loop.lower() != 'r':
            break