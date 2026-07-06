/*
 * assets/js/gerador-documentos.js — Tens Direito
 *
 * Motor único e genérico do Gerador de Documentos. Nenhuma minuta tem o
 * seu próprio JS — cada página só define um objecto de configuração
 * (CONFIG_DOCUMENTO) e chama GeradorDocumentos.iniciar(CONFIG_DOCUMENTO,
 * "id-do-contentor"). O motor:
 *
 *   1. Renderiza o formulário a partir de CONFIG_DOCUMENTO.campos
 *   2. Valida obrigatórios + padrões (regex) antes de gerar
 *   3. Gera o texto por template string com placeholders {{campo}}
 *   4. Mostra o resultado num <pre>, com botão Copiar (Clipboard API,
 *      fallback execCommand) e botão Descarregar .txt (Blob + URL)
 *
 * Restrições duras (mesmo padrão de checklist.js/share.js):
 *   - Zero chamadas de rede depois do load
 *   - Zero localStorage/sessionStorage — tudo em memória
 *   - Nenhuma biblioteca externa
 */
(function (global) {
  "use strict";

  var MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
  ];

  function pad2(n) {
    return n < 10 ? "0" + n : "" + n;
  }

  function dataHojeCurta() {
    var d = new Date();
    return pad2(d.getDate()) + "/" + pad2(d.getMonth() + 1) + "/" + d.getFullYear();
  }

  function dataHojeExtenso() {
    var d = new Date();
    return d.getDate() + " de " + MESES_PT[d.getMonth()] + " de " + d.getFullYear();
  }

  function formatarDataISOParaPT(iso) {
    var partes = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    if (!partes) {
      return iso || "";
    }
    return partes[3] + "/" + partes[2] + "/" + partes[1];
  }

  function elemento(tag, attrs, filhos) {
    var el = document.createElement(tag);
    attrs = attrs || {};
    for (var chave in attrs) {
      if (!Object.prototype.hasOwnProperty.call(attrs, chave)) {
        continue;
      }
      if (chave === "texto") {
        el.textContent = attrs[chave];
      } else if (chave.indexOf("data-") === 0 || chave.indexOf("aria-") === 0) {
        el.setAttribute(chave, attrs[chave]);
      } else {
        el[chave] = attrs[chave];
      }
    }
    (filhos || []).forEach(function (filho) {
      if (filho) {
        el.appendChild(filho);
      }
    });
    return el;
  }

  function idCampo(campo) {
    return "campo-" + campo.id;
  }

  function idErro(campo) {
    return "erro-" + campo.id;
  }

  function renderCampo(campo) {
    var grupo = elemento("div", { className: "gerador-form-group" });
    var label = elemento("label", { htmlFor: idCampo(campo), texto: campo.label + (campo.obrigatorio ? " *" : "") });
    grupo.appendChild(label);

    var controlo;
    var tipo = campo.tipo || "text";

    if (tipo === "textarea") {
      controlo = elemento("textarea", {
        id: idCampo(campo),
        name: campo.id,
        rows: campo.linhas || 5,
        placeholder: campo.placeholder || "",
      });
    } else if (tipo === "select") {
      controlo = elemento("select", { id: idCampo(campo), name: campo.id });
      if (!campo.obrigatorio) {
        controlo.appendChild(elemento("option", { value: "", texto: "— Seleccionar —" }));
      }
      (campo.opcoes || []).forEach(function (opcao) {
        controlo.appendChild(elemento("option", { value: opcao, texto: opcao }));
      });
    } else {
      controlo = elemento("input", {
        id: idCampo(campo),
        name: campo.id,
        type: tipo === "date" ? "date" : "text",
        placeholder: campo.placeholder || "",
      });
    }
    controlo.setAttribute("aria-describedby", idErro(campo));
    if (campo.obrigatorio) {
      controlo.setAttribute("aria-required", "true");
    }
    grupo.appendChild(controlo);

    if (campo.ajuda) {
      grupo.appendChild(elemento("small", { texto: campo.ajuda }));
    }

    var erro = elemento("small", { id: idErro(campo), className: "gerador-erro-campo", role: "alert" });
    grupo.appendChild(erro);

    return grupo;
  }

  function lerValorCampo(campo) {
    var el = document.getElementById(idCampo(campo));
    return el ? el.value : "";
  }

  function validarCampo(campo, valorBruto) {
    var valor = (valorBruto || "").trim();
    if (campo.obrigatorio && !valor) {
      return "O campo \"" + campo.label + "\" é obrigatório.";
    }
    if (valor && campo.padrao instanceof RegExp && !campo.padrao.test(valor)) {
      return campo.erro || ("O campo \"" + campo.label + "\" tem um formato inválido.");
    }
    return null;
  }

  function valorParaTemplate(campo, valorBruto) {
    var valor = (valorBruto || "").trim();
    if (!valor) {
      return campo.valorVazio !== undefined ? campo.valorVazio : "";
    }
    if (campo.tipo === "date") {
      return formatarDataISOParaPT(valor);
    }
    return valor;
  }

  function gerarTexto(template, valores) {
    return template.replace(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g, function (correspondencia, chave) {
      return Object.prototype.hasOwnProperty.call(valores, chave) ? valores[chave] : correspondencia;
    });
  }

  function copiarTexto(texto, botao, mensagemEl) {
    function sucesso() {
      if (mensagemEl) {
        mensagemEl.textContent = "✓ Copiado para a área de transferência.";
      }
    }
    function falha() {
      if (mensagemEl) {
        mensagemEl.textContent = "Não foi possível copiar automaticamente — selecciona o texto manualmente.";
      }
    }
    if (global.navigator && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(texto).then(sucesso, function () {
        if (!copiarComExecCommand(texto)) {
          falha();
        } else {
          sucesso();
        }
      });
      return;
    }
    if (copiarComExecCommand(texto)) {
      sucesso();
    } else {
      falha();
    }
  }

  function copiarComExecCommand(texto) {
    try {
      var area = document.createElement("textarea");
      area.value = texto;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.top = "-1000px";
      document.body.appendChild(area);
      area.select();
      var ok = document.execCommand("copy");
      document.body.removeChild(area);
      return ok;
    } catch (erro) {
      return false;
    }
  }

  function descarregarTexto(texto, nomeFicheiro) {
    var blob = new Blob([texto], { type: "text/plain;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var link = elemento("a", { href: url, download: nomeFicheiro });
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function iniciar(config, containerId) {
    var container = document.getElementById(containerId);
    if (!container) {
      return;
    }

    var form = elemento("form", { id: "form-" + config.id, noValidate: true });
    var resumoErros = elemento("div", { className: "gerador-erro-resumo", role: "alert", "aria-live": "polite" });
    form.appendChild(resumoErros);

    config.campos.forEach(function (campo) {
      form.appendChild(renderCampo(campo));
    });

    var botoesForm = elemento("div", { className: "gerador-btn-grupo" }, [
      elemento("button", { type: "submit", className: "gerador-btn gerador-btn-primary", texto: "📝 Gerar documento" }),
      elemento("button", { type: "reset", className: "gerador-btn gerador-btn-secondary", texto: "Limpar" }),
    ]);
    form.appendChild(botoesForm);
    container.appendChild(form);

    var resultadoWrap = elemento("div", { className: "gerador-resultado", id: "resultado-" + config.id, "aria-live": "polite" });
    var pre = elemento("pre", { className: "gerador-pre", id: "texto-gerado-" + config.id });
    var acoes = elemento("div", { className: "gerador-acoes" });
    var btnCopiar = elemento("button", { type: "button", className: "gerador-btn gerador-btn-secondary", id: "btn-copiar-" + config.id, texto: "📋 Copiar" });
    btnCopiar.disabled = true;
    var btnDescarregar = elemento("button", { type: "button", className: "gerador-btn gerador-btn-secondary", id: "btn-descarregar-" + config.id, texto: "⬇️ Descarregar .txt" });
    btnDescarregar.disabled = true;
    var mensagemFeedback = elemento("span", { className: "gerador-feedback", id: "feedback-" + config.id, "aria-live": "polite" });
    acoes.appendChild(btnCopiar);
    acoes.appendChild(btnDescarregar);
    acoes.appendChild(mensagemFeedback);
    resultadoWrap.appendChild(pre);
    resultadoWrap.appendChild(acoes);
    container.appendChild(resultadoWrap);

    var textoActual = "";

    btnCopiar.addEventListener("click", function () {
      copiarTexto(textoActual, btnCopiar, mensagemFeedback);
    });
    btnDescarregar.addEventListener("click", function () {
      descarregarTexto(textoActual, config.id + ".txt");
    });

    form.addEventListener("reset", function () {
      resultadoWrap.classList.remove("show");
      pre.textContent = "";
      textoActual = "";
      btnCopiar.disabled = true;
      btnDescarregar.disabled = true;
      mensagemFeedback.textContent = "";
      resumoErros.textContent = "";
      config.campos.forEach(function (campo) {
        var elErro = document.getElementById(idErro(campo));
        if (elErro) {
          elErro.textContent = "";
        }
      });
    });

    form.addEventListener("submit", function (evento) {
      evento.preventDefault();
      mensagemFeedback.textContent = "";

      var valores = {
        data_hoje: dataHojeCurta(),
        data_hoje_extenso: dataHojeExtenso(),
      };
      var erros = [];
      var primeiroInvalido = null;

      config.campos.forEach(function (campo) {
        var valorBruto = lerValorCampo(campo);
        var mensagemErro = validarCampo(campo, valorBruto);
        var elErro = document.getElementById(idErro(campo));
        if (mensagemErro) {
          erros.push(mensagemErro);
          if (elErro) {
            elErro.textContent = mensagemErro;
          }
          if (!primeiroInvalido) {
            primeiroInvalido = document.getElementById(idCampo(campo));
          }
        } else if (elErro) {
          elErro.textContent = "";
        }
        valores[campo.id] = valorParaTemplate(campo, valorBruto);
      });

      if (erros.length > 0) {
        resumoErros.textContent = "Corrige " + erros.length + " campo(s) antes de gerar o documento: " + erros.join(" ");
        resultadoWrap.classList.remove("show");
        if (primeiroInvalido) {
          primeiroInvalido.focus();
        }
        return;
      }

      resumoErros.textContent = "";
      textoActual = gerarTexto(config.template, valores).trim() + "\n";
      pre.textContent = textoActual;
      resultadoWrap.classList.add("show");
      btnCopiar.disabled = false;
      btnDescarregar.disabled = false;
      resultadoWrap.scrollIntoView({ behavior: "smooth", block: "start" });
      // Nota: ao contrário dos simuladores, este motor NUNCA dispara eventos
      // GA4 (nem qualquer outra chamada de rede) ao gerar o documento — é a
      // restrição dura "zero chamadas de rede depois do load" (ver
      // PROMPTGERADORDOCUMENTOSv1.md), verificada por teste de rede real.
    });
  }

  global.GeradorDocumentos = {
    iniciar: iniciar,
    // Expostas para os testes (Playwright avalia estas funções isoladas
    // sem precisar de simular toda a interacção do formulário).
    _gerarTexto: gerarTexto,
    _validarCampo: validarCampo,
    _valorParaTemplate: valorParaTemplate,
    _formatarDataISOParaPT: formatarDataISOParaPT,
  };
})(window);
