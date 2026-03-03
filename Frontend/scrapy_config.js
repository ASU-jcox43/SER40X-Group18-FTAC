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

    if (addLabel) {
        const label = document.createElement("label");
        label.for = key;
        const keys = key.split('.');
        label.textContent = keys[keys.length - 1];
        field.label = label;
    }

    if (Array.isArray(value)) {
        const innerForm = document.createElement("div");
        innerForm.classList.add('innerFormList');

        for (var i = 0; i < value.length; i++) {
            innerForm.appendChild(configFormField(`${key}#${i}`,value[i], addLabel=false).input);
            innerForm.appendChild(document.createElement("br"));
        }
        
        field.input = innerForm;
    }
    else if (value != null && typeof value == "object") {
        const innerForm = document.createElement("div");
        innerForm.classList.add('innerFormDict');
        entries = Object.entries(value);

        for (const [innerKey, innerValue] of entries) {
            const innerField = configFormField(`${key}.${innerKey}`, innerValue, addLabel=true);
            innerForm.appendChild(innerField.label);
            innerForm.appendChild(innerField.input);
            innerForm.appendChild(document.createElement("br"));
        }

        field.input = innerForm;
    }
    else {
        const input = document.createElement("input");
        input.name = key;

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
        nest(newConfigForm);
        e.preventDefault();
        const response = await fetch(`http://localhost:8000/scrapy_config?municipality=${values._id}`, {
            method: 'PUT',
            headers: {'Content-type': 'application/json'},
            body: ""
        });
        confirmation = document.createElement("p1");
        confirmation.textContent = "Scrapy config has been changed"
        selectedConfig.appendChild(confirmation)
    });

    return newConfigForm;
}

function nest(form) {
    const innerForms = form.querySelectorAll(`#${form.id} > div.innerFormDict`);
    const inputs = form.querySelectorAll(`#${form.id} > input`);
    console.log(innerForms);
    console.log(inputs);
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

    const exportButtonListItem = document.createElement("li");
    const exportAnchor = document.createElement("a");
    const exportButton = document.createElement("button");

    exportButtonListItem.classList.add(id);
    exportAnchor.href = `http://localhost:8000/scrapy_config/export_output?municipality=${municipality}`;
    exportAnchor.download = `${municipality}.csv`
    exportButton.textContent = "export list";

    exportAnchor.appendChild(exportButton);
    exportButtonListItem.appendChild(exportAnchor);

    scrapyOutputList.appendChild(exportButtonListItem);

    for (let item of list) {
        const listItem = document.createElement("li");
        const listItemAnchor = document.createElement("a");

        if (item.length > maxLinkLength) {
            listItemAnchor.textContent = `${item.slice(0, maxLinkLength/2)}...${item.slice(item.length - maxLinkLength/2 + 3, item.length)}`
        }
        else {
            listItemAnchor.textContent = item;
        }

        listItemAnchor.href = item;
        listItem.classList.add(id);
        listItem.appendChild(listItemAnchor);

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "remove";
        deleteButton.addEventListener("click", async (e) => {
            const response = await fetch(`http://localhost:8000/scrapy_config/output?municipality=${municipality}&link=${item}`, {
                method: 'DELETE',
                headers: {
                    'Content-type': 'application/json'
                }
            });

            if (await response.ok)
                deleteButton.parentElement.remove();
        });

        listItem.appendChild(deleteButton);
        scrapyOutputList.appendChild(listItem);
    }

    return scrapyOutputList;
}