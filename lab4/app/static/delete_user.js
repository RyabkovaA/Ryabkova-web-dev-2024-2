"use strict"

function fillModal(event) {
    let deleteUrl = event.relatedTarget.dataset.deleteUrl;
    let modalForm = event.target.querySelector("form");
    modalForm.action = deleteUrl;
    let userName = event.relatedTarget.dataset.userName; 
    let modalBody = event.target.querySelector("#modal-body-text");
    modalBody.textContent = 'Вы уверены, что хотите удалить пользователя ' + userName + '?'
}

window.onload = function() {
    let deleteModal = document.getElementById("delete-modal");
    deleteModal.addEventListener("show.bs.modal", fillModal);
}