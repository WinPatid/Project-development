// JavaScript สำหรับควบคุม Logic และ UI ทั้งหมด
// API Endpoint Base URL
const API_URL = 'http://127.0.0.1:5000/api';

let currentStep = 1;
let selectedService = '';

// 1. จัดการการเลือก Service
document.querySelectorAll('.service-card').forEach(card => {
    card.addEventListener('click', function() {
        document.querySelectorAll('.service-card').forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');
        selectedService = this.getAttribute('data-service');
        document.getElementById('selectedService').value = selectedService;
    });
});

// 2. จัดการการเปลี่ยน Step (ซ่อน/แสดง)
function updateStepIndicator() {
    document.querySelectorAll('.step-item').forEach((item, index) => {
        item.classList.remove('active');
        if (index + 1 === currentStep) {
            item.classList.add('active');
        }
    });
}

function nextStep(fromStep) {
    if (fromStep === 1) {
        if (!selectedService) {
            alert('กรุณาเลือกบริการที่ต้องการก่อน');
            return;
        }
        document.getElementById('serviceSelection').style.display = 'none';
        document.getElementById('customerForm').style.display = 'block';
        currentStep = 2;
    } else if (fromStep === 2) {
        // ตรวจสอบความถูกต้องของข้อมูล
        const form = document.getElementById('bookingForm');
        if (!form.checkValidity()) {
            alert('กรุณากรอกข้อมูลให้ครบถ้วน');
            form.reportValidity();
            return;
        }
        
        // เตรียมข้อมูลสรุป
        const firstName = document.getElementById('firstName').value;
        const lastName = document.getElementById('lastName').value;
        
        document.getElementById('summaryService').textContent = selectedService;
        document.getElementById('summaryFullName').textContent = `${firstName} ${lastName}`;
        document.getElementById('summaryPhone').textContent = document.getElementById('phone').value;
        document.getElementById('summaryEmail').textContent = document.getElementById('email').value;
        document.getElementById('summaryPlate').textContent = document.getElementById('licensePlate').value;
        document.getElementById('summaryDateTime').textContent = 
            document.getElementById('bookingDate').value + ' ' + document.getElementById('bookingTime').value;

        document.getElementById('customerForm').style.display = 'none';
        document.getElementById('confirmation').style.display = 'block';
        currentStep = 3;
    }
    updateStepIndicator();
}

function previousStep(fromStep) {
    if (fromStep === 2) {
        document.getElementById('customerForm').style.display = 'none';
        document.getElementById('serviceSelection').style.display = 'block';
        currentStep = 1;
    } else if (fromStep === 3) {
        document.getElementById('confirmation').style.display = 'none';
        document.getElementById('customerForm').style.display = 'block';
        currentStep = 2;
    }
    updateStepIndicator();
}

// 3. ฟังก์ชันยืนยันการจอง (เชื่อมต่อกับ API Backend) - TC-002, TC-006
async function confirmBooking() {
    const messageElement = document.getElementById('bookingMessage');
    
    // 1. รวบรวมข้อมูล
    const bookingData = {
        firstName: document.getElementById('firstName').value,
        lastName: document.getElementById('lastName').value,
        phone: document.getElementById('phone').value,
        email: document.getElementById('email').value,
        licensePlate: document.getElementById('licensePlate').value,
        bookingDate: document.getElementById('bookingDate').value,
        bookingTime: document.getElementById('bookingTime').value,
        selectedService: document.getElementById('selectedService').value,
    };
    
    try {
        messageElement.textContent = 'กำลังบันทึกข้อมูล...';
        messageElement.style.color = '#FF9800'; // สีส้ม
        
        // 2. เรียก API เพื่อบันทึกการจอง (TC-002)
        const response = await axios.post(`${API_URL}/book`, bookingData);
        
        messageElement.style.color = 'var(--primary-color)';
        messageElement.textContent = response.data.message;
        
        // 3. นำผู้ใช้กลับไปหน้า Tracking พร้อมเติมเบอร์โทรที่จองล่าสุด
        setTimeout(() => {
            showSection('statusTrackerSection');
            document.getElementById('trackingInput').value = bookingData.phone; 
            checkStatus(); // เรียก checkStatus ทันที
            messageElement.textContent = ''; 
        }, 2000);

    } catch (error) {
        messageElement.style.color = 'red';
        // TC-006: หากมีคิวซ้ำซ้อน Backend จะส่ง error 409
        if (error.response && error.response.status === 409) {
             messageElement.textContent = error.response.data.error; // ข้อความว่าคิวเต็มแล้ว
        } else {
             messageElement.textContent = `Error: ${error.response.data.error || 'การจองล้มเหลว'}`;
        }
    }
}

// 4. Logic สำหรับ Status Tracker (เชื่อมต่อกับ API Backend)
async function checkStatus() {
    const input = document.getElementById('trackingInput').value.trim(); 
    const resultBox = document.getElementById('statusResult');
    const infoDiv = document.getElementById('trackingInfo');
    const timelineSteps = document.querySelectorAll('#statusTimeline .timeline-step');
    const timelineLines = document.querySelectorAll('#statusTimeline .timeline-line');
    
    resultBox.style.display = 'none'; // ซ่อนผลลัพธ์เก่า

    if (!input) {
        infoDiv.innerHTML = `<p style="color: red; text-align: center; font-weight: bold;">กรุณาใส่เบอร์โทรศัพท์หรืออีเมล</p>`;
        resultBox.style.display = 'block';
        return;
    }

    try {
        infoDiv.innerHTML = `<p style="text-align: center;">กำลังค้นหาสถานะ...</p>`;
        resultBox.style.display = 'block';

        // เรียก API เพื่อดึงสถานะงานซ่อม
        const response = await axios.get(`${API_URL}/track?key=${input}`);
        const data = response.data.data;

        // --- แสดงข้อมูลลูกค้า ---
        document.getElementById('trackCustomerName').textContent = data.fullname;
        document.getElementById('trackCustomerDate').textContent = data.booking_date;
        document.getElementById('trackCustomerPlate').textContent = data.license_plate;
        document.getElementById('trackCustomerService').textContent = data.service_type; 
        
        // แสดงสถานะปัจจุบัน
        infoDiv.innerHTML = `
            <p style="font-size: 1.1em; color: var(--header-bg);"><b>สถานะปัจจุบัน:</b> <strong style="color: var(--primary-color);">${data.status}</strong></p>
        `;
        
        document.getElementById('statusTimeline').style.display = 'flex';
        
        // --- อัปเดต Timeline ---
        let foundCurrent = false;
        timelineSteps.forEach((step, index) => {
            const line = timelineLines[index];
            
            step.classList.remove('active-step');
            if (line) line.classList.remove('active-line');
            
            if (step.getAttribute('data-status') === data.status) {
                foundCurrent = true;
                step.classList.add('active-step'); 
            } else if (!foundCurrent) {
                step.classList.add('active-step'); 
                if (line) line.classList.add('active-line'); 
            }
        });

    } catch (error) {
        // ไม่พบข้อมูล
        infoDiv.innerHTML = `<p style="color: red; text-align: center; font-weight: bold;">ไม่พบข้อมูลการจองสำหรับ ${input}. กรุณาตรวจสอบเบอร์โทรศัพท์/อีเมล</p>`;
        document.getElementById('statusTimeline').style.display = 'none';
        resultBox.style.display = 'block';
    }
}

// ฟังก์ชันสลับหน้าจอหลัก (Booking vs Tracking)
function showSection(sectionId) {
    document.getElementById('bookingSection').style.display = 'none';
    document.getElementById('statusTrackerSection').style.display = 'none';
    
    document.getElementById(sectionId).style.display = 'block';
    document.getElementById(sectionId).scrollIntoView({ behavior: 'smooth' });
}


/* 5. Logic สำหรับ Login Modal (Pop-up) */
function openModal() {
    document.getElementById('loginModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('loginModal').style.display = 'none';
}

// Logic การตรวจสอบ Login (เชื่อมต่อกับ API Backend)
document.getElementById('employeeLoginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('modalUsername').value;
    const password = document.getElementById('modalPassword').value;
    const msg = document.getElementById('modalMessage');

    try {
        msg.textContent = 'กำลังตรวจสอบ...';
        msg.style.color = '#FF9800';

        // เรียก API Login (แทนที่ Logic เก่า)
        const response = await axios.post(`${API_URL}/login`, {
            username: username,
            password: password
        });
        
        msg.style.color = 'green';
        msg.textContent = `✅ Login สำเร็จ! Welcome, ${response.data.fullname}`;
        
        // นำไปที่ Admin Dashboard (เดี๋ยวเราจะแก้ไข admin_dashboard.html ต่อไป)
        setTimeout(() => {
            window.location.href = response.data.redirect; 
        }, 1500);

    } catch (error) {
        msg.style.color = 'red';
        msg.textContent = error.response.data.error || 'Login ล้มเหลว';
    }
});