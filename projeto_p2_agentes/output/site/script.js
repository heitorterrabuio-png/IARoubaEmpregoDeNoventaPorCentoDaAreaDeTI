document.addEventListener('DOMContentLoaded', () => {
  const contactForm = document.getElementById('contactForm');
  const formFeedback = document.getElementById('formFeedback');

  if (contactForm && formFeedback) {
    contactForm.addEventListener('submit', (event) => {
      event.preventDefault();

      const nomeInput = document.getElementById('nome');
      const emailInput = document.getElementById('email');
      const assuntoInput = document.getElementById('assunto');
      const mensagemInput = document.getElementById('mensagem');

      const nome = nomeInput.value.trim();
      const email = emailInput.value.trim();
      const assunto = assuntoInput.value.trim();
      const mensagem = mensagemInput.value.trim();

      formFeedback.className = 'form-feedback';

      if (!nome || !email || !assunto || !mensagem) {
        formFeedback.textContent = 'Por favor, preencha todos os campos obrigatórios antes de enviar.';
        formFeedback.classList.add('error');
        return;
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        formFeedback.textContent = 'Por favor, insira um endereço de e-mail válido.';
        formFeedback.classList.add('error');
        return;
      }

      formFeedback.textContent = 'Mensagem simulada com sucesso! Lembrete: este site é uma aplicação acadêmica demonstrativa e nenhum dado foi enviado.';
      formFeedback.classList.add('success');

      contactForm.reset();
    });
  }
});
