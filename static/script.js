document.addEventListener('DOMContentLoaded', () => {
    // 1. Kontrol Modal Video Showreel
    const modal = document.getElementById('videoModal');
    const openBtn = document.getElementById('openModalBtn');
    const closeBtn = document.querySelector('.close-modal');

    if (openBtn && modal) {
        openBtn.addEventListener('click', () => {
            modal.style.display = 'flex';
        });
    }

    if (closeBtn && modal) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // 2. Smooth Scroll untuk Navigasi Anchor
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // 3. Auto-hide Flash Messages setelah 4 detik
    const flashes = document.querySelectorAll('.flash');
    if (flashes.length > 0) {
        setTimeout(() => {
            flashes.forEach(flash => {
                flash.style.transition = 'opacity 0.5s ease';
                flash.style.opacity = '0';
                setTimeout(() => flash.remove(), 500);
            });
        }, 4000);
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const toasts = document.querySelectorAll(".flash");

    toasts.forEach((toast) => {
        // 1. Tambahkan tombol close (X) secara dinamis
        const closeBtn = document.createElement("button");
        closeBtn.className = "toast-close";
        closeBtn.innerHTML = "&times;";
        closeBtn.setAttribute("aria-label", "Tutup notifikasi");
        toast.appendChild(closeBtn);

        // 2. Tambahkan garis timer countdown di bagian bawah toast
        const progressBar = document.createElement("div");
        progressBar.className = "toast-progress";
        toast.appendChild(progressBar);

        // Fungsi untuk menyembunyikan dan menghapus elemen toast
        const removeToast = () => {
            toast.classList.add("toast-hide");
            setTimeout(() => {
                toast.remove();
            }, 400); // Tunggu animasi slide-out selesai (0.4s)
        };

        // Tutup saat tombol X diklik
        closeBtn.addEventListener("click", removeToast);

        // Tutup otomatis setelah 4 detik (4000 ms)
        setTimeout(removeToast, 4000);
    });
});