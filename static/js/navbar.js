// mobile menu
const burgerIcon = document.querySelector("#burger");
const navbarMenu = document.querySelector("#nav-links");

if (burgerIcon) {
    burgerIcon.addEventListener('click', () => {
        navbarMenu.classList.toggle('is-active');
    })
}
