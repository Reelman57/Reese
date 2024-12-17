from flask import Flask, request
import smtplib

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        elder_name = request.form['elder_name']
        family_name = request.form['family_name']
        health_concerns = request.form['health_concerns']
        social_activities = request.form['social_activities']
        temporal_needs = request.form['temporal_needs']
        spiritual_progress = request.form['spiritual_progress']
        additional_notes = request.form['additional_notes']

        # Format the email body
        email_body = f"""
        Elder's Quorum Ministering Report

        Elder's Name: {elder_name}
        Family Name: {family_name}

        Health Concerns:
        {health_concerns}

        Social Activities:
        {social_activities}

        Temporal Needs:
        {temporal_needs}

        Spiritual Progress:
        {spiritual_progress}

        Additional Notes:
        {additional_notes}
        """

        # Send the email (replace with your email credentials)
        sender_email = "eqp77216@gmail.com"
        recipient_email = "eqp77216@gmail.com"

        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:  
            smtp.starttls()
            smtp.login('eqp77216@gmail.com', 'ogla wwsg mnqw nmhn') 
            smtp.sendmail(sender_email, recipient_email, email_body)

        return "Report submitted successfully!"

    # Display the form
    return '''
        <html>
        <body>
        <h1>Elder's Quorum Ministering Report</h1>
        <form method="POST">
            <label for="elder_name">Elder's Name:</label>
            <input type="text" id="elder_name" name="elder_name" required><br><br>

            <button type="submit">Submit Report</button>
        </form>
        </body>
        </html>
    '''

if __name__ == "__main__":
    app.run(debug=True)
    
