import base64
import pytest
from playwright.sync_api import Page, expect

URL = "file:///Users/humita/Projects/git/cultivo/index.html"

@pytest.fixture(autouse=True)
def setup_page(page: Page):
    """Carga la página fresca en cada test."""
    page.goto(URL)
    expect(page.locator("#ttl")).to_contain_text("Cultivo")


# ─── Helpers ────────────────────────────────────────────────────────────────

def crear_cliente(page: Page, nombre: str):
    """Crea un cliente y navega a su pantalla de detalle."""
    page.locator("#fab").click()
    expect(page.locator("#m-nc")).to_be_visible()
    page.locator("#nc-nom").fill(nombre)
    page.locator("#m-nc button:has-text('Continuar')").click()
    expect(page.locator("#ttl")).to_have_text(nombre)


# ─── CUJ 1: Cargar un pedido nuevo (nuevo UX inline) ────────────────────────

def test_cuj1_cargar_nuevo_pedido(page: Page):
    crear_cliente(page, "Cliente Test")

    # La lista de artículos debería estar visible (todas las flores en fi-off)
    expect(page.locator(".fi").first).to_be_visible()

    # Encontrar la fila de Aleli e incrementar cantidad
    aleli_row = page.locator(".fi").filter(has_text="Aleli")
    plus_btn = aleli_row.locator(".fi-plus")
    plus_btn.click()

    # El item se activa: debe mostrar cantidad 1
    expect(aleli_row.locator(".fi-q")).to_have_text("1")
    expect(aleli_row).to_have_class("fi fi-on")

    # Volver a inicio y verificar que el resumen del cliente muestra la flor
    page.locator("#back-btn").click()
    card = page.locator(".ccard").filter(has_text="Cliente Test")
    expect(card).to_contain_text("1 flores")


# ─── CUJ 2: Checklist de Armado (Empaquetado) ────────────────────────────────

def test_cuj2_checklist_empaquetado(page: Page):
    crear_cliente(page, "Cliente Pk")

    # Incrementar cantidad de Crisantemo fideo
    cris_row = page.locator(".fi").filter(has_text="Crisantemo fideo")
    cris_row.locator(".fi-plus").click()
    expect(cris_row.locator(".fi-q")).to_have_text("1")

    # El círculo de empaquetado debe estar visible
    pk_circle = cris_row.locator(".fi-pk")
    expect(pk_circle).to_be_visible()

    # Marcar como empaquetado
    pk_circle.click()
    expect(cris_row.locator(".circ")).to_have_class("circ pk")

    # Volver a inicio y verificar el contador de empaquetado
    page.locator("#back-btn").click()
    card = page.locator(".ccard").filter(has_text="Cliente Pk")
    expect(card).to_contain_text("1 empaq ✓")


# ─── CUJ 3: Finalizar y Despachar Pedido ─────────────────────────────────────

def test_cuj3_finalizar_pedido(page: Page):
    crear_cliente(page, "Cliente Final")

    # Agregar un artículo para que la tarjeta sea visible
    page.locator(".fi").filter(has_text="Aleli").locator(".fi-plus").click()
    page.locator("#back-btn").click()

    card = page.locator(".ccard").filter(has_text="Cliente Final")
    card.locator("button", has_text="Finalizar").click()

    expect(card).to_have_class("ccard done")
    expect(card).to_contain_text("✓ Listo")


# ─── CUJ 4: Control de Cobranzas y Saldos ────────────────────────────────────

def test_cuj4_cobranzas_saldos(page: Page):
    crear_cliente(page, "Cliente Banco")

    # Agregar Rosa importada x 60cm: 2 paq
    rosa_row = page.locator(".fi").filter(has_text="Rosa importada x 60cm")
    rosa_row.locator(".fi-plus").click()
    rosa_row.locator(".fi-plus").click()

    # Editar el precio del artículo a 3000 via modal
    rosa_row.locator(".fi-edit").click()
    expect(page.locator("#m-precio")).to_be_visible()
    page.locator("#mp-prec").fill("3000")
    page.locator("#m-precio button:has-text('Guardar')").click()

    # El total debe ser $6000 — verificar en el header de la orden
    expect(page.locator("#dtot")).to_have_text("$ 6.000")

    # Abrir el modal de Pagos
    page.locator("#actbar button:has-text('Pagos')").click()
    expect(page.locator("#ps-tot")).to_have_text("$ 6.000")

    # Registrar pago parcial
    page.locator("#pag-monto").fill("2000")
    page.locator("#pag-nota").fill("Adelanto")
    page.locator("#m-pagos button:has-text('+ Agregar')").click()

    expect(page.locator("#ps-pag")).to_have_text("$ 2.000")
    expect(page.locator("#ps-sal")).to_have_text("$ 4.000")
    page.locator("#m-pagos button:has-text('Cerrar')").click()

    # Verificar en pantalla principal
    page.locator("#back-btn").click()
    card = page.locator(".ccard").filter(has_text="Cliente Banco")
    expect(card).to_contain_text("Saldo: $ 4.000")


# ─── CUJ 5: Generación de Recibo / Presupuesto PDF ───────────────────────────

def test_cuj5_generar_recibo_modal(page: Page):
    crear_cliente(page, "Cliente PDF")
    page.locator(".fi").filter(has_text="Aleli").locator(".fi-plus").click()

    # Abrir modal de Recibo
    page.locator("#actbar button:has-text('Recibo')").click()
    expect(page.locator("#m-recibo")).to_be_visible()
    expect(page.locator("#r-cli")).to_have_value("Cliente PDF")

    page.locator("#m-recibo button:has-text('Cancelar')").click()


# ─── CUJ 6: Calcular Recuento Diario ─────────────────────────────────────────

def test_cuj6_recuento_diario(page: Page):
    # Cliente A → Tulipán x4
    crear_cliente(page, "Cliente A")
    tulipan_row = page.locator(".fi").filter(has_text="Tulipán")
    for _ in range(4):
        tulipan_row.locator(".fi-plus").click()
    page.locator("#back-btn").click()

    # Cliente B → Aleli x6
    crear_cliente(page, "Cliente B")
    aleli_row = page.locator(".fi").filter(has_text="Aleli")
    for _ in range(6):
        aleli_row.locator(".fi-plus").click()

    # Ir a Recuento
    page.locator("#nav-recuento").click()

    rbody = page.locator("#rbody")
    expect(rbody).to_contain_text("Tulipán")
    expect(rbody).to_contain_text("4")
    expect(rbody).to_contain_text("Aleli")
    expect(rbody).to_contain_text("6")


# ─── CUJ 7: Gestión de Catálogo y Precios ────────────────────────────────────

def test_cuj7_catalogo_crud(page: Page):
    page.locator("#nav-catalogo").click()

    page.locator("button:has-text('+ Agregar flor')").click()
    page.locator("#mf-nom").fill("Orquídea Test")
    page.locator("#mf-prec").fill("5000")
    page.locator("#m-flor button", has_text="Guardar").click()
    # Esperar que el modal se cierre antes de filtrar
    expect(page.locator("#m-flor")).not_to_be_visible()

    page.locator("input[placeholder='Buscar flor...']").fill("Orquídea Test")
    flor_item = page.locator("#flist .li").first
    expect(flor_item).to_contain_text("Orquídea Test")
    expect(flor_item).to_contain_text("$ 5.000 x unidad")


# ─── CUJ 8: Configuración del Comercio ───────────────────────────────────────

def test_cuj8_configuracion_negocio(page: Page):
    page.locator(".tright button[onclick=\"showScreen('config')\"]").click()

    page.locator("#cfg-nom").fill("Florería Los Pinos")
    page.locator("#cfg-tel").fill("111-222-3333")
    page.locator("#sc-config button", has_text="Guardar").click()

    page.locator(".tright button[onclick=\"showScreen('config')\"]").click()
    expect(page.locator("#cfg-nom")).to_have_value("Florería Los Pinos")
    expect(page.locator("#cfg-tel")).to_have_value("111-222-3333")


# ─── CUJ 9: Descuentos Globales de Pedido ────────────────────────────────────

def test_cuj9_descuentos(page: Page):
    crear_cliente(page, "Cliente Promo")

    # Agregar dos flores para un subtotal de 4000 (asumiendo Rosa importada que fue 3000 antes, o lo ponemos a mano)
    rosa_row = page.locator(".fi").filter(has_text="Rosa importada x 60cm")
    rosa_row.locator(".fi-plus").click()
    
    rosa_row.locator(".fi-edit").click()
    expect(page.locator("#m-precio")).to_be_visible()
    page.locator("#mp-prec").fill("1000")
    page.locator("#m-precio button:has-text('Guardar')").click()

    # Total ahora es 1000
    expect(page.locator("#dtot")).to_have_text("$ 1.000")

    # Aplicar descuento del 10%
    page.locator("#actbar button:has-text('Descuento')").click()
    expect(page.locator("#m-desc")).to_be_visible()
    page.locator("#md-pct").fill("10")
    page.locator("#md-reflejar").check() # Reflejado en recibo
    page.locator("#m-desc button:has-text('Guardar')").click()
    expect(page.locator("#m-desc")).not_to_be_visible()

    # El subtotal (1000) tachado y el total (900) visible
    dtot = page.locator("#dtot")
    expect(dtot).to_contain_text("$ 1.000")
    expect(dtot).to_contain_text("$ 900")

    # Vamos a inicio a verificar tarjeta
    page.locator("#back-btn").click()
    card_index = page.locator(".ccard").filter(has_text="Cliente Promo")
    expect(card_index.locator(".ctot")).to_have_text("$ 900")


# ─── CUJ 10: Decrementar flor hasta 0 ────────────────────────────────────────

def test_cuj10_decrementar_flor(page: Page):
    crear_cliente(page, "Cliente Decr")
    aleli_row = page.locator(".fi").filter(has_text="Aleli")

    # Incrementar x2
    aleli_row.locator(".fi-plus").click()
    aleli_row.locator(".fi-plus").click()
    expect(aleli_row.locator(".fi-q")).to_have_text("2")
    expect(aleli_row).to_have_class("fi fi-on")

    # Decrementar a 1
    aleli_row.locator(".fi-btn").first.click()
    expect(aleli_row.locator(".fi-q")).to_have_text("1")

    # Decrementar a 0 → item vuelve a estado inactivo
    aleli_row.locator(".fi-btn").first.click()
    expect(aleli_row.locator(".fi-q")).to_have_text("")
    expect(aleli_row).to_have_class("fi fi-off")


# ─── CUJ 11: Eliminar cliente del día ────────────────────────────────────────

def test_cuj11_eliminar_cliente_dia(page: Page):
    crear_cliente(page, "Cliente Borrar")
    page.locator(".fi").filter(has_text="Aleli").locator(".fi-plus").click()
    page.locator("#back-btn").click()

    card = page.locator(".ccard").filter(has_text="Cliente Borrar")
    expect(card).to_be_visible()

    page.once("dialog", lambda d: d.accept())
    card.locator("button", has_text="Eliminar").click()

    expect(card).not_to_be_visible()


# ─── CUJ 12: Reabrir un pedido finalizado ────────────────────────────────────

def test_cuj12_reabrir_pedido(page: Page):
    crear_cliente(page, "Cliente Reabrir")
    page.locator(".fi").filter(has_text="Aleli").locator(".fi-plus").click()
    page.locator("#back-btn").click()

    card = page.locator(".ccard").filter(has_text="Cliente Reabrir")
    card.locator("button", has_text="Finalizar").click()
    expect(card).to_have_class("ccard done")

    # Reabrir el pedido
    card.locator("button", has_text="Reabrir").click()
    expect(card).not_to_have_class("ccard done")
    expect(card).not_to_contain_text("✓ Listo")


# ─── CUJ 13: Eliminar pago registrado ────────────────────────────────────────

def test_cuj13_eliminar_pago(page: Page):
    crear_cliente(page, "Cliente DelPago")
    page.locator(".fi").filter(has_text="Aleli").locator(".fi-plus").click()

    page.locator("#actbar button:has-text('Pagos')").click()
    page.locator("#pag-monto").fill("500")
    page.locator("#m-pagos button:has-text('+ Agregar')").click()
    expect(page.locator("#ps-pag")).to_have_text("$ 500")

    # Eliminar el pago (acepta el confirm)
    page.once("dialog", lambda d: d.accept())
    page.locator("#pag-lista .bic.red").first.click()

    expect(page.locator("#ps-pag")).to_have_text("$ 0")
    expect(page.locator("#pag-empty")).to_be_visible()


# ─── CUJ 14: Editar flor en catálogo ─────────────────────────────────────────

def test_cuj14_editar_flor_catalogo(page: Page):
    page.locator("#nav-catalogo").click()

    # Agregar una nueva flor
    page.locator("button:has-text('+ Agregar flor')").click()
    page.locator("#mf-nom").fill("Flor Editable")
    page.locator("#mf-prec").fill("2000")
    page.locator("#m-flor button", has_text="Guardar").click()
    expect(page.locator("#m-flor")).not_to_be_visible()

    # Buscarla y abrir edición
    page.locator("input[placeholder='Buscar flor...']").fill("Flor Editable")
    flor_item = page.locator("#flist .li").first
    flor_item.locator("button").first.click()  # botón ✏️

    expect(page.locator("#m-flor")).to_be_visible()
    expect(page.locator("#mf-ttl")).to_have_text("Editar flor")

    # Cambiar precio
    page.locator("#mf-prec").fill("3500")
    page.locator("#m-flor button", has_text="Guardar").click()
    expect(page.locator("#m-flor")).not_to_be_visible()

    # Verificar precio actualizado en la lista
    page.locator("input[placeholder='Buscar flor...']").fill("Flor Editable")
    expect(page.locator("#flist .li").first).to_contain_text("$ 3.500 x unidad")


# ─── CUJ 15: Catálogo — gestión de clientes ──────────────────────────────────

def test_cuj15_catalogo_clientes(page: Page):
    page.locator("#nav-catalogo").click()
    page.locator(".tab", has_text="Clientes").click()

    # Agregar cliente al catálogo
    page.locator("button:has-text('+ Agregar cliente')").click()
    expect(page.locator("#m-cli")).to_be_visible()
    page.locator("#mc-nom").fill("Mayorista Test")
    page.locator("#m-cli button", has_text="Guardar").click()
    expect(page.locator("#m-cli")).not_to_be_visible()
    expect(page.locator("#klist")).to_contain_text("Mayorista Test")

    # Eliminar el cliente
    cliente_item = page.locator("#klist .li").filter(has_text="Mayorista Test")
    page.once("dialog", lambda d: d.accept())
    cliente_item.locator(".bic.red").click()
    expect(page.locator("#klist")).not_to_contain_text("Mayorista Test")


# ─── Botón Instalar App ───────────────────────────────────────────────────────

MOCK_PROMPT = """() => {
    window._promptCalled = false;
    const e = new Event('beforeinstallprompt');
    e.preventDefault = () => {};
    e.prompt = () => { window._promptCalled = true; return Promise.resolve(); };
    e.userChoice = Promise.resolve({ outcome: 'accepted' });
    window.dispatchEvent(e);
}"""


def test_install_btn_hidden_by_default(page: Page):
    """El botón está oculto por defecto (no hay beforeinstallprompt)."""
    expect(page.locator("#btn-install")).not_to_be_visible()


def test_install_btn_visible_after_beforeinstallprompt(page: Page):
    """El botón aparece cuando el navegador dispara beforeinstallprompt."""
    page.evaluate(MOCK_PROMPT)
    expect(page.locator("#btn-install")).to_be_visible()


def test_install_btn_calls_prompt_on_click(page: Page):
    """Al hacer clic se llama a prompt() del evento diferido."""
    page.evaluate(MOCK_PROMPT)
    page.locator("#btn-install").click()
    assert page.evaluate("() => window._promptCalled")


def test_install_btn_hides_after_user_choice(page: Page):
    """El botón desaparece una vez que el usuario responde al diálogo."""
    page.evaluate(MOCK_PROMPT)
    expect(page.locator("#btn-install")).to_be_visible()
    page.locator("#btn-install").click()
    expect(page.locator("#btn-install")).not_to_be_visible()


def test_install_btn_hides_on_appinstalled(page: Page):
    """El botón desaparece si el evento appinstalled se dispara (app ya instalada)."""
    page.evaluate(MOCK_PROMPT)
    expect(page.locator("#btn-install")).to_be_visible()
    page.evaluate("() => window.dispatchEvent(new Event('appinstalled'))")
    expect(page.locator("#btn-install")).not_to_be_visible()


# ─── Logo upload ──────────────────────────────────────────────────────────────

# Minimal 1x1 white PNG for testing (69 bytes)
TEST_LOGO = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4"
    "//8/AAX+Av4N70a4AAAAAElFTkSuQmCC"
)

def go_to_config(page: Page):
    page.locator(".tright button[onclick=\"showScreen('config')\"]").click()


def test_logo_preview_oculto_por_defecto(page: Page):
    """Sin logo guardado, el preview está oculto."""
    go_to_config(page)
    expect(page.locator("#logo-preview-wrap")).not_to_be_visible()


def test_logo_upload_muestra_preview(page: Page):
    """Al subir una imagen se muestra el preview."""
    go_to_config(page)
    page.locator("#cfg-logo-file").set_input_files(
        {"name": "logo.jpg", "mimeType": "image/jpeg", "buffer": TEST_LOGO}
    )
    expect(page.locator("#logo-preview-wrap")).to_be_visible()
    src = page.locator("#logo-preview").get_attribute("src")
    assert src.startswith("data:image/jpeg")


def test_logo_se_persiste_al_recargar(page: Page):
    """El logo guardado sigue visible al volver a abrir Config."""
    go_to_config(page)
    page.locator("#cfg-logo-file").set_input_files(
        {"name": "logo.jpg", "mimeType": "image/jpeg", "buffer": TEST_LOGO}
    )
    expect(page.locator("#logo-preview-wrap")).to_be_visible()

    # Navegar a otra pantalla y volver a Config
    page.locator("#nav-catalogo").click()
    go_to_config(page)
    expect(page.locator("#logo-preview-wrap")).to_be_visible()


def test_logo_eliminar(page: Page):
    """El botón Eliminar quita el logo y oculta el preview."""
    go_to_config(page)
    page.locator("#cfg-logo-file").set_input_files(
        {"name": "logo.jpg", "mimeType": "image/jpeg", "buffer": TEST_LOGO}
    )
    expect(page.locator("#logo-preview-wrap")).to_be_visible()
    page.locator("#logo-preview-wrap button").click()
    expect(page.locator("#logo-preview-wrap")).not_to_be_visible()
