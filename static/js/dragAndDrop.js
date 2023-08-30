document.getElementById('input').addEventListener('drop', dropHandler);
document.getElementById('input').addEventListener('dragover', dragOverHandler);

function dropHandler(ev) {
    ev.preventDefault();
    fileInput.files = ev.dataTransfer.files;
    fileForm.submit();
}

function dragOverHandler(ev) {
    ev.preventDefault();
}

const form = document.getElementById('fileForm');
document.getElementById('fileInput').addEventListener('change', () => {
    form.submit();
});