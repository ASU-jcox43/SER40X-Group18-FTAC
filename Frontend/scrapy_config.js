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
    const field = document.createElement("div");

    if (addLabel) {
        const label = document.createElement("label");
        label.for = key;
        label.textContent = key;
        field.appendChild(label);
    }

    const input = document.createElement("input");
    input.id = key;
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
        case 'string':
            input.type = "text";
            input.value = value;
            break;
        default:
            break;
    }

    if (value == null) {
        input.type = "text";
        field.appendChild(input);
    }
    else if (Array.isArray(value)) {
        const innerForm = document.createElement("div");
        innerForm.style.paddingLeft = '2em'

        for (var i = 0; i < value.length; i++) {
            innerForm.appendChild(configFormField(`${key}_${i}`,value[i], addLabel=false));
        }
        
        field.appendChild(innerForm);
    }
    else if (typeof value === "object") {
        const innerForm = document.createElement("div");
        innerForm.style.paddingLeft = '2em'
        entries = Object.entries(value);

        for (const [innerKey, innerValue] of entries) {
            innerForm.appendChild(configFormField(innerKey, innerValue, addLabel=true));
        }

        field.appendChild(innerForm);
    }
    else {
        field.appendChild(input);
    }

    field.appendChild(document.createElement("br"));

    return field;
}

function configForm(values, id = "scrapyConfigForm") {
    const resultForm = document.createElement("form");
    resultForm.id = id;
    resultForm.noValidate = true;
    const valuesCopy = structuredClone(values);
    delete valuesCopy._id;
    resultForm.appendChild(configFormField(values._id, valuesCopy, addLabel=true))

    return resultForm;
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