document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => loadMailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => loadMailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => loadMailbox('archive'));
  document.querySelector('#compose').addEventListener('click', composeEmail);

  // By default, load the inbox
  loadMailbox('inbox');
});

function composeEmail() {

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
        loadMailbox('sent');
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }
}

function loadMailbox(mailbox) {
  
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
    renderEmailBox(emails);
  })
  .catch(error => {
    console.error('Error:', error);
  });
}

function renderEmailBox(emails) {
  // Get container element
  const container = document.querySelector('#emails-view');
  
  // Clear container
  container.innerHTML = '';
  
  // Iterate through emails
  emails.forEach(email => {
    const mailDiv = document.createElement('div');

    mailDiv.classList.add('email-item');
    
    // Change background color to grey after mail is read
    if (!email.read) {
      mailDiv.classList.add('email-unread');
    } else {
      mailDiv.classList.add('email-read');
    }
    
    mailDiv.innerHTML = `
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
    
    mailDiv.addEventListener('click', function() {
      console.log(`Mail #${email.id} has been clicked!`);
      viewEmail(email);
    });
    container.append(mailDiv);
  });
}


function viewEmail(email){
  // Show the email and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#email-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';

  // Get and render email
  fetch(`emails/${email.id}`)
  .then(response => response.json())
  .then(email => {
    console.log(email);
    renderEmailView(email);
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
  .then(result => {
      // Print result
      console.log(result); 
  })
  .catch(error => {
    console.error('Error:', error);
  });
}

function renderEmailView(email){
  // Get container element
  const container = document.querySelector('#email-view');
  
  // Clear container
  container.innerHTML = '';
  
  // Create email view element
  const emailView = document.createElement('div');
  emailView.classList.add('email-view');

  emailView.innerHTML = `
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

  container.append(emailView);

  // Archive and unarchive
  // Only show archive button if the user is not the sender (not in sent mailbox)
  if (email.sender !== document.querySelector('#user-email').innerHTML) {
    //Create archive button
    const button = document.createElement('button');
    button.classList.add('archive-button');
    button.textContent = email.archived ? 'Unarchive' : 'Archive';
    container.append(button);

    // Click button to archive email
    button.addEventListener('click', () => toggleArchive(email));
  }

  // Reply button
  //Create reply button
  const replyButton = document.createElement('button');
  replyButton.classList.add('reply-button');
  replyButton.textContent = 'Reply';
  container.append(replyButton);

  // Click reply button to reply email
  replyButton.addEventListener('click', () => reply(email));
}

function toggleArchive(email) {
  fetch(`/emails/${email.id}`, {
    method: 'PUT',
    body: JSON.stringify({
      archived: !email.archived  // Toggle the archived status
    })
  })
  .then(result => {
    console.log(result);
    loadMailbox('inbox');
  })
  .catch(error => {
    console.error('Error:', error);
  });
}


function reply(email){
  composeEmail();

  // Prefill the composition form
  document.querySelector('#compose-recipients').value = `${email.sender}`;
  document.querySelector('#compose-subject').value = 
    email.subject.startsWith('Re:') ? email.subject : `Re: ${email.subject}`;
  document.querySelector('#compose-body').value = `
    On ${email.timestamp} ${email.sender} wrote: 
    ${email.body}
  `;
}