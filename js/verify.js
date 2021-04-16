'use strict'


let handednessInput = document.getElementsByName("handedness")[0];


handednessInput.addEventListener("input", () => {
    if (handednessInput.textContent !== "Lol") {
        handednessInput.setCustomValidity("Nur Lol ist erlaubt");
    }
})
