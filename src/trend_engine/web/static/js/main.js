/* Trend Engine — Main JS */

function showToast(msg, duration = 2500) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, duration);
}

function copyContent() {
    const el = document.getElementById('generatedContent');
    if (!el) return;
    navigator.clipboard.writeText(el.innerText).then(() => showToast('📋 Đã copy!'));
}
