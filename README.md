# Grocery_Helper
# 🛒 Grocery Price Comparison App
Demo link: https://drive.google.com/file/d/1wlDo8RRxon1t77M7k0X-CjCj_X_RPLeH/view?usp=sharing
Compare grocery prices across platforms like Blinkit, Zepto, Swiggy, JioMart, Dmart, and Bigbasket.  
Built with **Streamlit** for the frontend and an **Azure Function** backend with Cosmos DB caching. A locally running version also

---

## 🚀 [Features](https://drive.google.com/file/d/1wlDo8RRxon1t77M7k0X-CjCj_X_RPLeH/view?usp=sharing)

- 📷 Upload your grocery bill and auto-extract product names.
- 🔍 Compare real-time prices across multiple Indian grocery platforms.
- 🏆 See the best deals and delivery times for each product.
- 🗂️ Smart cart matrix for optimized shopping.
- ⚡ Fast, thanks to Azure Function API and Cosmos DB caching.

---

## 🏗️ Project Structure

├── function_app.py # Azure Function backend (Python)<br>
├── pages/<br>
│ ├── 1_upload_bill.py # Streamlit Page 1: Upload bill<br>
│ ├── 2_compare_prices.py # Streamlit Page 2: Price comparison<br>
│ └── 3_final_Cart.py # Streamlit Page 3: Optimized cart<br>
├── requirements.txt # Python dependencies<br>
├── .gitignore<br>
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

## 📦 Dependencies

- streamlit
- pandas or SQL
- requests
- beautifulsoup4 (for image url)
- azure-functions
- azure-cosmos
- python-dotenv
---

## 🙏 Acknowledgements

- [Big Thanks to QC](http://quickcompare.in/)
- Azure Functions & Cosmos DB
- Streamlit Community
- [Dmart](https://www.dmart.in/), [Blinkit](https://blinkit.com/), [Zepto](https://www.zeptonow.com/), [JioMart](https://www.jiomart.com/), [Bigbasket](https://www.bigbasket.com/), [Swiggy](https://www.swiggy.com/)
- Open Source Libraries
