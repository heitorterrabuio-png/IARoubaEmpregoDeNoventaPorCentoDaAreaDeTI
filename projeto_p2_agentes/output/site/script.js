document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('form-contato');
  var feedbackArea = document.getElementById('feedback-mensagem');

  if (!form || !feedbackArea) {
    return;
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();

    var campoNome = document.getElementById('nome');
    var campoEmail = document.getElementById('email');
    var campoAssunto = document.getElementById('assunto');
    var campoMensagem = document.getElementById('mensagem');

    var nome = campoNome ? campoNome.value.trim() : '';
    var email = campoEmail ? campoEmail.value.trim() : '';
    var assunto = campoAssunto ? campoAssunto.value.trim() : '';
    var mensagem = campoMensagem ? campoMensagem.value.trim() : '';

    // resetar estado visual do feedback
    feedbackArea.className = 'feedback-area';
    feedbackArea.textContent = '';

    // validacao de campos vazios
    if (!nome || !email || !assunto || !mensagem) {
      exibirFeedback('Por favor, preencha todos os campos do formulário antes de enviar.', 'erro');
      return;
    }

    // validacao de formato de e-mail com regex segura
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      exibirFeedback('Por favor, insira um endereço de e-mail válido (exemplo: nome@dominio.com).', 'erro');
      return;
    }

    // mensagem de sucesso demonstrativa
    exibirFeedback('Mensagem enviada com sucesso! Esta é uma demonstração acadêmica e nenhum dado foi transmitido para servidores externos.', 'sucesso');

    // limpeza dos campos
    form.reset();
  });

  function exibirFeedback(texto, tipo) {
    feedbackArea.textContent = texto;
    feedbackArea.className = 'feedback-area ' + tipo;
  }
});
