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
  document.querySelector('#email-view').style.display = 'none';
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
  document.querySelector('#email-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'none';

  // Show the mailbox name
  document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

  // Get emails
  fetch(`emails/${mailbox}`)
  .then(response => response.json())
  .then(emails => {
    console.log(emails);
    render_email_box(emails);
  })
  .catch(error => {
    console.error('Error:', error);
  });
}

function render_email_box(emails) {
  // Get container element
  const container = document.querySelector('#emails-view');
  
  // Clear container
  container.innerHTML = '';
  
  // Iterate through emails
  emails.forEach(email => {
    const mail_div = document.createElement('div');

    mail_div.classList.add('email-item');
    
    // Change background color to grey after mail is read
    if (!email.read) {
      mail_div.classList.add('email-unread');
    } else {
      mail_div.classList.add('email-read');
    }
    
    mail_div.innerHTML = `
      <div class="email-sender">
        ${email.sender}
      </div>
      <div class="email-subject">
        ${email.subject}
      </div>
      <div class="email-timestamp">
        ${email.timestamp}
      </div>
    `;
    
    mail_div.addEventListener('click', function() {
      console.log(`Mail #${email.id} has been clicked!`);
      view_email(email);
    });
    container.append(mail_div);
  });
}


function view_email(email){
  // Show the email and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#email-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';

  // Get email
  fetch(`emails/${email.id}`)
  .then(response => response.json())
  .then(email => {
    console.log(email);
    render_email_view(email);
  })
  .catch(error => {
    console.error('Error:', error);
  });

  // Mark email as read
  fetch(`/emails/${email.id}`, {
    method: 'PUT',
    body: JSON.stringify({
      read: true
    })
  })
  .then(response => response.json())
  .then(result => {
      // Print result
      console.log(result); 
  })
  .catch(error => {
    console.error('Error:', error);
  });
}

function render_email_view(email){
  // Get container element
  const container = document.querySelector('#email-view');
  
  // Clear container
  container.innerHTML = '';
  
  // Create email view element
  const email_view = document.createElement('div');
  email_view.classList.add('email-view');

  email_view.innerHTML = `
    <div class="email-sender">
      <strong>From:</strong> ${email.sender}
    </div>
    <div class="email-recipients">
      <strong>To:</strong> ${email.recipients}
    </div>
    <div class="email-subject">
      <strong>Subject:</strong> ${email.subject}
    </div>
    <div class="email-timestamp">
      <strong>Timestamp:</strong> ${email.timestamp}
    </div>
    <div class="email-body"> 
      ${email.body}
    </div>
  `;
 
  container.append(email_view);
}