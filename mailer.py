from dotenv import dotenv_values
from datetime import datetime
import traceback
import base64
import sendgrid
from pymongo import MongoClient
from content import genHtml, text, subject

config = dotenv_values(".env")

connection = MongoClient(config["mongodb_url"])
db = connection.get_database("mailer")

senders = db.get_collection("senders")
companies = db.get_collection("toSend")


def sendEmail(company_name, company_emails, from_email, api_key):

    sg = sendgrid.SendGridAPIClient(api_key=api_key)

    personalizations = list(
        map(lambda email: {"to": [{"email": email}]}, company_emails))

    attachment = open("brochure.pdf", "rb").read()
    attachment = base64.b64encode(attachment).decode()

    email = {
        "personalizations": personalizations,
        "from": {"email": from_email},
        "subject": subject,
        "content": [
            {
                "type": "text/plain",
                "value": text.format(company_name=company_name)
            },
            {
                "type": "text/html",
                "value": genHtml(company_name=company_name)
            }
        ],
        "attachments": [{
            "content": attachment,
            "disposition": "attachment",
            "filename": "brochure.pdf",
            "name": "Brochure",
            "type": "pdf"
        }]
    }
    try:
        response = sg.client.mail.send.post(request_body=email)
        if not response.status_code == 202:
            print(company_name)
            print(company_emails)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        res = {"company_name": company_name, "emails": company_emails,
               "status_code": response.status_code, "timestamp": str(datetime.now())}
        print(res)
        companies.update_one({"name": company_name}, {"$set": {"sent": True}})
        senders.update_one({"email": from_email}, {"$push": {"sent": res}})
    except:
        print(company_name)
        print(company_emails)
        traceback.print_exc()
        exit(0)


def main():
    for sender in senders.find():
        count = 0
        from_email = sender["email"]
        api_key = sender["api_key"]
        for company in companies.find():

            if len(company["emails"]) == 1:
                if (count + len(company["emails"])) > 100:
                    break

                if not company["sent"]:
                    sendEmail(
                        company_name=company["name"], company_emails=company["emails"], from_email=from_email, api_key=api_key)
                    count += len(company["emails"])
                    print(count)


main()
