// services/emailService.js
const nodemailer = require('nodemailer');

/**
 * Send email
 * @param {Object} emailData - Email data
 * @param {String} emailData.to - Recipient email
 * @param {String} emailData.subject - Email subject
 * @param {String} emailData.text - Plain text version
 * @param {String} emailData.html - HTML version
 * @returns {Promise}
 */
const sendEmail = async (emailData) => {
  // Create transporter
  let transporter;
  
  if (process.env.NODE_ENV === 'production') {
    // Production configuration (e.g., SendGrid, Mailgun, etc.)
    transporter = nodemailer.createTransport({
      service: process.env.EMAIL_SERVICE,
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASSWORD
      }
    });
  } else {
    // Development configuration (ethereal.email)
    const testAccount = await nodemailer.createTestAccount();
    
    transporter = nodemailer.createTransport({
      host: 'smtp.ethereal.email',
      port: 587,
      secure: false,
      auth: {
        user: testAccount.user,
        pass: testAccount.pass
      }
    });
  }
  
  // Email options
  const mailOptions = {
    from: process.env.EMAIL_FROM || '"WhatsApp Messenger" <noreply@whatsappmessenger.com>',
    to: emailData.to,
    subject: emailData.subject,
    text: emailData.text,
    html: emailData.html
  };
  
  // Send email
  const info = await transporter.sendMail(mailOptions);
  
  // Log URL for development
  if (process.env.NODE_ENV !== 'production') {
    console.log('Preview URL: %s', nodemailer.getTestMessageUrl(info));
  }
  
  return info;
};

module.exports = sendEmail;