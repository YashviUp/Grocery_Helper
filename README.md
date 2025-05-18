# Grocery_Helper
# 🛒 Grocery Price Comparison App
Demo link: https://drive.google.com/file/d/1wlDo8RRxon1t77M7k0X-CjCj_X_RPLeH/view?usp=sharing
Compare grocery prices across platforms like Blinkit, Zepto, Swiggy, JioMart, Dmart, and Bigbasket.  
Built with **Streamlit** for the frontend and an **Azure Function** backend with Cosmos DB caching.

---

## 🚀 Features

- 📷 Upload your grocery bill and auto-extract product names.
- 🔍 Compare real-time prices across multiple Indian grocery platforms.
- 🏆 See the best deals and delivery times for each product.
- 🗂️ Smart cart matrix for optimized shopping.
- ⚡ Fast, thanks to Azure Function API and Cosmos DB caching.

---

## 🏗️ Project Structure

├── function_app.py # Azure Function backend (Python)
├── pages/
│ ├── 1_upload_bill.py # Streamlit Page 1: Upload bill
│ ├── 2_compare_prices.py # Streamlit Page 2: Price comparison
│ └── 3_final_Cart.py # Streamlit Page 3: Optimized cart
├── requirements.txt # Python dependencies
├── .gitignore
├── README.md

(Requires [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local))

---

## ☁️ Deployment

### Azure Function

1. Deploy using Azure CLI or VS Code Azure Functions extension.
2. Set environment variables (`COSMOS_ENDPOINT`, `COSMOS_KEY`) in Azure portal.

### Streamlit

- Deploy on [Streamlit Community Cloud](https://share.streamlit.io/) or your own server.
- Ensure the frontend can reach your Azure Function API endpoint.

---

## 📝 Usage

1. **Upload your grocery bill** (image or PDF).
2. **Review and confirm** the extracted items.
3. **Compare prices** and see the best deals.
4. **View your optimized cart** and checkout recommendations.

---

## 🛡️ Security

- **No secrets are stored in code or git history.**
- All sensitive info is managed via environment variables or Azure Key Vault.
- [GitHub push protection](https://docs.github.com/en/code-security/secret-scanning/push-protection) is enabled.

---

## 📦 Dependencies

- streamlit
- pandas
- requests
- beautifulsoup4
- azure-functions
- azure-cosmos
- python-dotenv

See `requirements.txt` for full list.

---

## 🤝 Contributing

Pull requests and suggestions are welcome!  
Please open an issue to discuss your ideas.

---

## 📄 License

[MIT License](LICENSE)

---

## 🙏 Acknowledgements

- [Big Thanks to QC](http://quickcompare.in/)
- Azure Functions & Cosmos DB
- Streamlit Community
- [Dmart](https://www.dmart.in/), [Blinkit](https://blinkit.com/), [Zepto](https://www.zeptonow.com/), [JioMart](https://www.jiomart.com/), [Bigbasket](https://www.bigbasket.com/), [Swiggy](https://www.swiggy.com/)
- Open Source Libraries

---

*Made with ❤️ in India*
