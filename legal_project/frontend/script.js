function uploadPDF() {
    alert("PDF uploaded.\n(Text extraction will be handled by backend)");
    
    // Dummy extracted text
    document.getElementById("extractedText").value =
        "The accused was found in possession of illegal substances under the Narcotic Drugs Act...";
}

function classifyCase() {
    // Dummy prediction
    document.getElementById("prediction").innerText = "drug";

    // Dummy similar cases
    const list = document.getElementById("similarCases");
    list.innerHTML = "";

    ["case_017.txt", "case_019.txt", "case_024.txt"].forEach(c => {
        const li = document.createElement("li");
        li.innerText = c;
        list.appendChild(li);
    });
}
