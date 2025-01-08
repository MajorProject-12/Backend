document.addEventListener('DOMContentLoaded', () => {
    // JS for the profile dropdown menu items
    const profile = document.getElementById('profile');
    const dropdownMenu = document.getElementById('dropdown-menu');
    const dropdownIcon = document.getElementById('dropdown-icon');

    // JS for the notification dropdown menu items
    const notifications = document.getElementById('notifications');
    const notificationDropdownMenu = document.getElementById('notification-dropdown-menu');

    // JS for the burger menu dropdown
    const burgerMenu = document.getElementById('burger-menu');
    const burgerDropdown = document.getElementById('burger-dropdown');

    // Flags to track dropdown state
    let isProfileDropdownOpen = false;
    let isNotificationDropdownOpen = false;
    let isBurgerDropdownOpen = false;

    // Function to close all dropdowns
    function closeAllDropdowns() {
        // Close profile dropdown
        if (dropdownMenu && dropdownMenu.classList.contains('show')) {
            dropdownMenu.classList.remove('show');
            dropdownIcon.style.transform = 'rotate(0deg)';
            const menuItems = dropdownMenu.querySelectorAll('.menu-item');
            menuItems.forEach(item => {
                item.style.opacity = '0'; // Reset opacity
                item.style.transform = 'translateY(10px)'; // Reset position
            });
            setTimeout(() => {
                dropdownMenu.style.display = 'none';
            }, 300);
            isProfileDropdownOpen = false;
        }

        // Close notification dropdown
        if (notificationDropdownMenu && notificationDropdownMenu.classList.contains('show')) {
            notificationDropdownMenu.classList.remove('show');
            const menuItems = notificationDropdownMenu.querySelectorAll('.menu-item');
            menuItems.forEach(item => {
                item.style.opacity = '0'; // Reset opacity
                item.style.transform = 'translateY(10px)'; // Reset position
            });
            setTimeout(() => {
                notificationDropdownMenu.style.display = 'none';
            }, 300);
            isNotificationDropdownOpen = false;
        }

        // Close burger dropdown
        if (burgerDropdown && burgerDropdown.classList.contains('show')) {
            burgerDropdown.classList.remove('show');
            const menuItems = burgerDropdown.querySelectorAll('.menu-item');
            menuItems.forEach(item => {
                item.style.opacity = '0'; // Reset opacity
                item.style.transform = 'translateY(10px)'; // Reset position
            });
            setTimeout(() => {
                burgerDropdown.style.display = 'none';
            }, 300);
            isBurgerDropdownOpen = false;
        }
    }

    // Toggle dropdown menu on profile click
    if (profile) {
        profile.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent the click from bubbling up to the document

            // Close other dropdowns if they are open
            if (!isProfileDropdownOpen) {
                closeAllDropdowns();
            }

            // Toggle the profile dropdown
            if (!isProfileDropdownOpen) {
                dropdownMenu.style.display = 'block';
                setTimeout(() => {
                    dropdownMenu.classList.add('show');
                    const menuItems = dropdownMenu.querySelectorAll('.menu-item');
                    menuItems.forEach((item, index) => {
                        setTimeout(() => {
                            item.style.opacity = '1'; // Show item
                            item.style.transform = 'translateY(0)'; // Move to original position
                        }, index * 100); // Delay for each item
                    });
                }, 10);
                dropdownIcon.style.transform = 'rotate(180deg)';
                isProfileDropdownOpen = true;
            } else {
                closeAllDropdowns();
            }
        });
    }

    // Toggle notification dropdown menu on notifications click
    if (notifications) {
        notifications.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent the click from bubbling up to the document

            // Close other dropdowns if they are open
            if (!isNotificationDropdownOpen) {
                closeAllDropdowns();
            }

            // Toggle the notification dropdown
            if (!isNotificationDropdownOpen) {
                notificationDropdownMenu.style.display = 'block';
                setTimeout(() => {
                    notificationDropdownMenu.classList.add('show');
                    const menuItems = notificationDropdownMenu.querySelectorAll('.menu-item');
                    menuItems.forEach((item, index) => {
                        setTimeout(() => {
                            item.style.opacity = '1'; // Show item
                            item.style.transform = 'translateY(0)'; // Move to original position
                        }, index * 100); // Delay for each item
                    });
                }, 10);
                isNotificationDropdownOpen = true;
            } else {
                closeAllDropdowns();
            }
        });
    }

    // Toggle burger dropdown menu on burger menu click
    if (burgerMenu) {
        burgerMenu.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent the click from bubbling up to the document

            // Close other dropdowns if they are open
            if (!isBurgerDropdownOpen) {
                closeAllDropdowns();
            }

            // Toggle the burger dropdown
            if (!isBurgerDropdownOpen) {
                burgerDropdown.style.display = 'block';
                setTimeout(() => {
                    burgerDropdown.classList.add('show');
                    const menuItems = burgerDropdown.querySelectorAll('.menu-item');
                    menuItems.forEach((item, index) => {
                        setTimeout(() => {
                            item.style.opacity = '1'; // Show item
                            item.style.transform = 'translateY(0)'; // Move to original position
                        }, index * 100); // Delay for each item
                    });
                }, 10);
                isBurgerDropdownOpen = true;
            } else {
                closeAllDropdowns();
            }
        });
    }

    // Close dropdowns when clicking outside of them
    document.addEventListener('click', (event) => {
        const isClickInsideDropdown = dropdownMenu.contains(event.target) || notificationDropdownMenu.contains(event.target) || burgerDropdown.contains(event.target);
        const isClickOnProfileOrNotification = profile.contains(event.target) || notifications.contains(event.target) || burgerMenu.contains(event.target);

        if (!isClickInsideDropdown && !isClickOnProfileOrNotification) {
            closeAllDropdowns();
        }
    });

    // Add resize event listener to close burger dropdown on screen resize
    window.addEventListener('resize', () => {
        const screenWidth = window.innerWidth;
        if (screenWidth > 600 && burgerDropdown && burgerDropdown.classList.contains('show')) {
            closeAllDropdowns();
        }
    });
});