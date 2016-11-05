/**
 * Created by haibin on 14-5-29.
 */

function openModal(fadeId, modalId) {
    $('#' + fadeId).show();
    $('#' + modalId).show();
}

function closeModal(fadeId, modalId) {
    $('#' + fadeId).hide();
    $('#' + modalId).hide();
}