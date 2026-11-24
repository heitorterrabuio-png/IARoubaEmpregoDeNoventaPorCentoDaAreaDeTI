document.addEventListener('DOMContentLoaded', function () {
    const contactForm = document.getElementById('contactForm');
    const formFeedback = document.getElementById('formFeedback');

    if (contactForm) {
        contactForm.addEventListener('submit', function (event) {
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
            formFeedback.textContent = '';

            if (!nome || !email || !assunto || !mensagem) {
                formFeedback.className = 'form-feedback error';
                formFeedback.textContent = 'Por favor, preencha todos os campos obrigatórios do formulário.';
                return;
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                formFeedback.className = 'form-feedback error';
                formFeedback.textContent = 'Por favor, insira um endereço de e-mail válido.';
                return;
            }

            formFeedback.className = 'form-feedback success';
            formFeedback.textContent = 'Mensagem simulada com sucesso! (Atenção: Aplicação acadêmica demonstrativa, nenhum dado foi enviado externamente).';
            
            contactForm.reset();
        });
    }
});
