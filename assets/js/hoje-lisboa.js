// Data de hoje em Europe/Lisbon, partilhada pela página do calendário de
// pagamentos e pela barra "Próximo pagamento" da homepage: o calendário vira
// de mês à meia-noite de Lisboa, qualquer que seja o fuso do aparelho (#280).
// Sem suporte a Intl com timeZone (navegador muito antigo), usa a data do
// aparelho.
window.tdHojeLisboa = function (agora) {
  agora = agora || new Date();
  try {
    var partes = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Europe/Lisbon', year: 'numeric', month: '2-digit', day: '2-digit'
    }).formatToParts(agora);
    var v = {};
    for (var i = 0; i < partes.length; i++) v[partes[i].type] = partes[i].value;
    if (/^\d{4}$/.test(v.year) && /^\d{2}$/.test(v.month) && /^\d{2}$/.test(v.day)) {
      return { ano: +v.year, mes: +v.month, dia: +v.day, chave: v.year + '-' + v.month };
    }
  } catch (e) { /* cai para a data do aparelho */ }
  var mes = agora.getMonth() + 1;
  return {
    ano: agora.getFullYear(), mes: mes, dia: agora.getDate(),
    chave: agora.getFullYear() + '-' + ('0' + mes).slice(-2)
  };
};
