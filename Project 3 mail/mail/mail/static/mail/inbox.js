document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', compose_email);

  // By default, load the inbox
  load_mailbox('inbox');
});

function compose_email() {

  // Show compose view and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';

  // Clear out composition fields
  document.querySelector('#compose-recipients').value = '';
  document.querySelector('#compose-subject').value = '';
  document.querySelector('#compose-body').value = '';

  // Sent email
  document.querySelector('#compose-form').onsubmit = function(event){
    event.preventDefault();

    // Check input form
    const recipients = document.querySelector('#compose-recipients').value.trim();
    const subject = document.querySelector('#compose-subject').value.trim();
    const body = document.querySelector('#compose-body').value.trim();

    if (!recipients){
      alert('Recipients field is required.');
      return;
    }
    if (!subject){
      alert('Subject field is required.');
      return;
    }
    if (!body){
      alert('Body field is required.');
      return;
    }

    // POST request
    fetch('/emails', {
      method: 'POST',
      body: JSON.stringify({
          recipients: document.querySelector('#compose-recipients').value,
          subject: document.querySelector('#compose-subject').value,
          body: document.querySelector('#compose-body').value
      })
    })
    .then(response => response.json())
    .then(result => {
        // Print result
        console.log(result); 
        //Load user's sent box
        load_mailbox('sent');
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }
}

function load_mailbox(mailbox) {
  
  // Show the mailbox and hide other views
  document.querySelector('#emails-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';

  // Show the mailbox name
  document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

  // Get emails
  fetch(`emails/${mailbox}`)
  .then(response => response.json())
  .then(emails => {
    console.log(emails);
    render_email_div(emails);
  })
  .catch(error => {
    console.error('Error:', error);
  });
}

function render_email_div(emails) {
  // Get container element
  const container = document.querySelector('#emails-view');
  
  // Clear container
  container.innerHTML = '';
  
  // Iterate through emails
  emails.forEach(mail => {
    const mail_div = document.createElement('div');

    mail_div.classList.add('email-item');
    
    // Change background color to grey after mail is read
    if (!mail.read) {
      mail_div.classList.add('email-unread');
    } else {
      mail_div.classList.add('email-read');
    }
    
    mail_div.innerHTML = `
      <div class="email-sender">
        ${mail.sender}
      </div>
      <div class="email-subject">
        ${mail.subject}
      </div>
      <div class="email-timestamp">
        ${mail.timestamp}
      </div>
    `;
    
    mail_div.addEventListener('click', function() {
      console.log(`Mail #${mail.id} has been clicked!`);
    });
    
    container.append(mail_div);
  });
}