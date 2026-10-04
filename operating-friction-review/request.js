(function () {
  const form = document.getElementById('review-request');
  if (!form) return;
  form.addEventListener('submit', function (event) {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const details = new FormData(form);
    const body = ['Hello John,', '', 'I would like to arrange a call about an Operating Friction Review.', '',
      'Name: ' + details.get('name'), 'Work email: ' + details.get('email'),
      'Organization: ' + details.get('organization'), '',
      'Workflow to review:', details.get('workflow'), '',
      'Timezone and preferred way to connect: ' + details.get('preference')].join('\r\n');
    window.location.href = 'mailto:hello@guildatelier.com?subject=' + encodeURIComponent('Operating Friction Review — call request') + '&body=' + encodeURIComponent(body);
    document.getElementById('request-status').textContent = 'Your email app has been requested. Please review and send the email to complete your request. If it does not open, use the email address below. Your details remain here until you leave or refresh this page.';
  });
})();
