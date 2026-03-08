const searchForm = document.getElementById('searchForm');
const municipalitySearch = document.getElementById('municipalitySearch');
const selectedConfig = document.getElementById('selectedConfig');
const municipalityLinkList = document.getElementById('municipalityLinkList');
document.addEventListener('DOMContentLoaded', () => {
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = Object.fromEntries(new FormData(searchForm));
        const response = await fetch(`http://localhost:8000/scrapy_config?municipality=${input.searchInput.toLowerCase()}`);
        const responseBody = await response.json();

        const searchResult = document.getElementById('municipalitySearchResult');
        if (searchResult != null)
            municipalitySearch.removeChild(searchResult);
        municipalitySearch.appendChild(municipalitySearchResultList('municipalitySearchResult', responseBody));
    })
})

function municipalitySearchResultList(id, searchResults) {
    const municipalitySearchResultList = document.createElement("ul");
    municipalitySearchResultList.id = id;
    for (let result of searchResults) {
        var listItem = document.createElement("li");
        listItem.textContent = result["_id"];
        listItem.id = result["_id"];
        listItem.addEventListener("click", async (e) => {
            e.preventDefault();

            while (selectedConfig.hasChildNodes())
                selectedConfig.removeChild(selectedConfig.firstChild);

            selectedConfig.appendChild(configForm(result));

            while (municipalityLinkList.hasChildNodes())
                municipalityLinkList.removeChild(municipalityLinkList.firstChild);

            const response = await fetch(`http://localhost:8000/scrapy_config/output?municipality=${result["_id"]}`);
            const responseBody = await response.json();

            municipalityLinkList.appendChild(scrapyOutputList(responseBody, result["_id"]));
        });
        municipalitySearchResultList.appendChild(listItem);
    }

    return municipalitySearchResultList;
}

function configFormField(key, value, addLabel = true) {
    const field = {}
    const subkeys = key.split('-');
    const labelText = subkeys[subkeys.length - 1];


    if (addLabel) {
        const label = document.createElement("label");
        label.for = key;
        label.textContent = labelText;
        field.label = label;
    }

    if (Array.isArray(value)) {
        const innerForm = document.createElement("div");
        innerForm.classList.add(labelText, 'innerFormList');
        innerForm.id = key;

        for (var i = 0; i < value.length; i++) {
            innerForm.appendChild(configFormField(`${key}-${i}`,value[i], addLabel=false).input);
            innerForm.appendChild(document.createElement("br"));
        }
        
        field.input = innerForm;
    }
    else if (value != null && typeof value == "object") {
        const innerForm = document.createElement("div");
        innerForm.classList.add(labelText, 'innerFormDict');
        innerForm.id = key;

        entries = Object.entries(value);

        for (const [innerKey, innerValue] of entries) {
            const innerField = configFormField(`${key}-${innerKey}`, innerValue, addLabel=true);
            innerForm.appendChild(innerField.label);
            innerForm.appendChild(innerField.input);
            innerForm.appendChild(document.createElement("br"));
        }

        field.input = innerForm;
    }
    else {
        const input = document.createElement("input");
        input.classList.add(labelText);
        input.id = key;

        switch (typeof value) {
            case 'boolean':
                input.type = "checkbox";
                input.checked = value;
                break;
            case 'number':
                input.type = "number";
                input.value = value;
                break;
            default: // strings and null
                input.type = "text";
                input.value = value || "";
                break;
        }

        field.input = input;
    }

    return field;
}

function configForm(values, id = "scrapyConfigForm") {
    const newConfigForm = document.createElement("form");
    newConfigForm.id = id;
    newConfigForm.noValidate = true;
    const valuesCopy = structuredClone(values);
    delete valuesCopy._id;

    const rootField = configFormField(values._id, valuesCopy, addLabel=true);
    newConfigForm.appendChild(rootField.label);
    newConfigForm.appendChild(rootField.input);

    const submitConfigButton = document.createElement("button");
    submitConfigButton.type = "submit"
    submitConfigButton.textContent = "save config"
    newConfigForm.appendChild(submitConfigButton);
    newConfigForm.appendChild(document.createElement("br"));

    newConfigForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        formData = JSON.stringify(configFormData(newConfigForm)[values._id]);
        console.log(formData);
        
        const response = await fetch(`http://localhost:8000/scrapy_config?municipality=${values._id}`, {
            method: 'PUT',
            headers: {'Content-type': 'application/json'},
            body: formData
        });
        
        confirmation = document.createElement("p1");
        confirmation.textContent = "Scrapy config has been changed"
        selectedConfig.appendChild(confirmation)
    });

    return newConfigForm;
}

function configFormData(form, formData = {}) {
    const inputs = form.querySelectorAll(`#${form.id} > input`);
    const innerForms = form.querySelectorAll(`#${form.id} > div.innerFormDict`);
    const lists = form.querySelectorAll(`#${form.id} > div.innerFormList`);
    const isArray = Array.isArray(form);

    for (const input of inputs) {
        var formValue = input.value;
        
        switch (input.type) {
            case "checkbox":
                formValue = input.checked
                break;
            case "number":
                formValue = Number(input.value)
                break;
            default:
                break;
        }

        if (isArray) {
            formData.push(formValue);
        }
        else {
            formData[input.classList[0]] = formValue;
        }
    }

    for (const innerForm of innerForms) {
        if (isArray) {
            formData.push({});
            configFormData(innerForm, formData[formData.length - 1]);
        }
        else {
            formData[innerForm.classList[0]] = {};
            configFormData(innerForm, formData[innerForm.classList[0]]);
        }
    }

    for (const list of lists) {
        if (isArray) {
            formData.push([]);
            configFormData(list, formData[formData.length - 1]);
        }
        else {
            formData[list.classList[0]] = [];
            configFormData(list, formData[list.classList[0]]);
        }
    }

    return formData;
}

function scrapyOutputList(list, municipality, id = "scrapyOutputList", maxLinkLength = 50) {
    if (list == null || list.length == 0) {
        const scrapyOutputList = document.createElement("p");
        scrapyOutputList.textContent = "no links found";
        scrapyOutputList.id = id;
        return scrapyOutputList;
    }

    const scrapyOutputList = document.createElement("ul");
    scrapyOutputList.id = id;

    const exportli = exportLinksListItem(municipality);
    exportli.classList.add(id);
    const addli = addLinkListItem(municipality, maxLinkLength);
    addli.classList.add(id);
    scrapyOutputList.appendChild(exportli);
    scrapyOutputList.appendChild(addli);

    for (let item of list) {
        const outputli = storedLinkListItem(municipality, item, maxLinkLength);
        outputli.classList.add(id);
        scrapyOutputList.appendChild(outputli);
    }

    return scrapyOutputList;
}

function storedLinkListItem(municipality, link, maxLinkLength = 50) {
    const listItem = document.createElement("li");
    const listItemAnchor = document.createElement("a");
    
    if (link.length > maxLinkLength) {
        listItemAnchor.textContent = `${link.slice(0, maxLinkLength/2)}...${link.slice(link.length - maxLinkLength/2 + 3, link.length)}`
    }
    else {
        listItemAnchor.textContent = link;
    }

    listItemAnchor.href = link;
    listItem.appendChild(listItemAnchor);

    const deleteButton = document.createElement("button");
    deleteButton.textContent = "remove";
    deleteButton.addEventListener("click", async (e) => {
        const response = await fetch(`http://localhost:8000/scrapy_config/output?municipality=${municipality}&link=${link}`, {
            method: 'DELETE',
            headers: {
                'Content-type': 'application/json'
            }
        });

        if (await response.ok)
            deleteButton.parentElement.remove();
    });

    listItem.appendChild(deleteButton);
    
    return listItem;
}

function addLinkListItem(municipality) {
    const addLinkItem = document.createElement("li");
    const addLinkButton = document.createElement("button");
    addLinkButton.textContent = "add link";
    addLinkItem.appendChild(addLinkButton);

    addLinkButton.addEventListener("click", async (e) => {
        var addLinkInput = addLinkItem.querySelector("#add_link_input");
        if (addLinkInput) {
            fetch(`http://localhost:8000/scrapy_config/output?municipality=${municipality}&link=${addLinkInput.value}`, {
                method: 'POST',
                headers: {
                    'Content-type': 'application/json'
                }
            }).then(res => res.json()).then(body => {
                console.log(body["new_link"]);
                addLinkInput.remove();
                addLinkButton.textContent = "add link";
                addLinkItem.after(storedLinkListItem(municipality, body["new_link"]));
            });
        }
        else {
            addLinkInput = document.createElement('input');
            addLinkInput.id = 'add_link_input';
            addLinkItem.insertBefore(addLinkInput, addLinkButton);
            addLinkButton.textContent = "save";
        }
    });

    return addLinkItem;
}

function exportLinksListItem(municipality) {
    const exportButtonListItem = document.createElement("li");
    const exportAnchor = document.createElement("a");
    const exportButton = document.createElement("button");
    exportAnchor.href = `http://localhost:8000/scrapy_config/export_output?municipality=${municipality}`;
    exportAnchor.download = `${municipality}.csv`
    exportButton.textContent = "export list";

    exportAnchor.appendChild(exportButton);
    exportButtonListItem.appendChild(exportAnchor);

    return exportButtonListItem;
}