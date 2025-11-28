let selectedService = "";

function selectService(service) {
selectedService = service;
document.querySelectorAll('.service-option').forEach(div => div.style.border = "2px solid transparent");

event.target.closest('.service-option').style.border = "2px solid #0066ff";
}

function nextStep(step) {
if (step === 1 && selectedService === "") {
alert("กรุณาเลือกบริการก่อน");
return;
}

document.getElementById('serviceSelection').style.display = "none";
document.getElementById('customerForm').style.display = step === 1 ? "block" : "none";
document.getElementById('confirmation').style.display = step === 2 ? "block" : "none";

if (step === 2) updateSummary();
}

function previousStep(step) {
document.getElementById('serviceSelection').style.display = step === 2 ? "block" : "none";
document.getElementById('customerForm').style.display = step === 3 ? "block" : "none";
document.getElementById('confirmation').style.display = "none";
}

function updateSummary() {
document.getElementById('summaryService').innerText = selectedService;
document.getElementById('summaryName').innerText = document.getElementById('fullName').value;
document.getElementById('summaryPhone').innerText = document.getElementById('phone').value;
document.getElementById('summaryEmail').innerText = document.getElementById('email').value;
document.getElementById('summaryPlate').innerText = document.getElementById('licensePlate').value;

const date = document.getElementById('bookingDate').value;
const time = document.getElementById('bookingTime').value;
document.getElementById('summaryDateTime').innerText = `${date} - ${time}`;
}

function confirmBooking() {
document.getElementById('bookingMessage').innerText = "✔ การจองสำเร็จ!";
}

function openModal() {
document.getElementById('loginModal').style.display = 'flex';
}

function closeModal() {
document.getElementById('loginModal').style.display = 'none';
}