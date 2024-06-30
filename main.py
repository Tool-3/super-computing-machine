import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

# Initialize session state
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=['Item', 'Quantity', 'Price', 'Supplier', 'Category'])

if 'credit_books' not in st.session_state:
    st.session_state.credit_books = pd.DataFrame(columns=['Customer', 'Amount Due', 'Due Date'])

if 'sales' not in st.session_state:
    st.session_state.sales = pd.DataFrame(columns=['Customer', 'Item', 'Quantity', 'Price', 'Date'])

# Sidebar menu
st.sidebar.title('Navigation')
page = st.sidebar.radio('Go to', ['Inventory Management', 'Credit Books', 'Quotation Builder', 'Sales Management', 'Analytics'])

# Inventory Management Page
if page == 'Inventory Management':
    st.title('Inventory Management')
    st.image('logo.png', width=200)

    st.header('Add Item')
    item = st.text_input('Item Name')
    quantity = st.number_input('Quantity', min_value=0, step=1)
    price = st.number_input('Price (INR)', min_value=0.0, step=0.1)
    supplier = st.text_input('Supplier')
    category = st.selectbox('Category', ['Stationery', 'Office Supplies', 'Art Supplies'])

    if st.button('Add Item'):
        # Data validation
        if not item or not supplier or not category:
            st.error('Please fill in all fields.')
        elif quantity < 0 or price < 0:
            st.error('Quantity and price must be non-negative.')
        else:
            new_item = pd.DataFrame({'Item': [item], 'Quantity': [quantity], 'Price': [price], 'Supplier': [supplier], 'Category': [category]})
            st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
            st.success(f'Item {item} added successfully!')

    st.header('Remove Item')
    if not st.session_state.inventory.empty:
        remove_item = st.selectbox('Select Item to Remove', st.session_state.inventory['Item'])
        if st.button('Remove Item'):
            st.session_state.inventory = st.session_state.inventory[st.session_state.inventory['Item'] != remove_item]
            st.success(f'Item {remove_item} removed successfully!')
    else:
        st.write("No items to remove.")

    st.header('Inventory')
    search_term = st.text_input('Search Inventory')
    filtered_inventory = st.session_state.inventory[st.session_state.inventory['Item'].str.contains(search_term, case=False, na=False)]

    sort_by = st.selectbox('Sort By', ['Item', 'Quantity', 'Price', 'Supplier', 'Category'])
    filter_by = st.selectbox('Filter By', ['All Categories'] + list(st.session_state.inventory['Category'].unique()))

    if filter_by != 'All Categories':
        filtered_inventory = filtered_inventory[filtered_inventory['Category'] == filter_by]

    filtered_inventory = filtered_inventory.sort_values(by=sort_by)

    page_size = st.number_input('Page Size', min_value=1, step=1, value=10)
    total_pages = (len(filtered_inventory) + page_size - 1) // page_size
    page_number = st.number_input('Page Number', min_value=1, max_value=total_pages, step=1, value=1)
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size

    st.dataframe(filtered_inventory.iloc[start_index:end_index])

    if not filtered_inventory.empty:
        st.subheader('Detailed View')
        detailed_item = st.selectbox('Select Item to View Details', filtered_inventory['Item'])
        detailed_data = st.session_state.inventory[st.session_state.inventory['Item'] == detailed_item]
        st.write(detailed_data)

    total_value = (filtered_inventory['Quantity'] * filtered_inventory['Price']).sum()
    st.write(f'Total Inventory Value: ₹{total_value:.2f}')

    low_stock_items = filtered_inventory[filtered_inventory['Quantity'] < 10]
    if not low_stock_items.empty:
        st.warning('The following items are low in stock:')
        st.dataframe(low_stock_items)

    if st.button('Download Inventory as CSV'):
        csv = st.session_state.inventory.to_csv(index=False)
        st.download_button(label='Download CSV', data=csv, file_name='inventory.csv', mime='text/csv')

# Credit Books Page
elif page == 'Credit Books':
    st.title('Credit Books')

    st.subheader('Add Credit Entry')
    customer = st.text_input('Customer Name')
    amount_due = st.number_input('Amount Due (INR)', min_value=0.0, step=0.1)
    due_date = st.date_input('Due Date')

    if st.button('Add Credit Entry'):
        if not customer or amount_due <= 0 or not due_date:
            st.error('Please fill in all fields.')
        else:
            new_credit = pd.DataFrame({'Customer': [customer], 'Amount Due': [amount_due], 'Due Date': [due_date]})
            st.session_state.credit_books = pd.concat([st.session_state.credit_books, new_credit], ignore_index=True)
            st.success(f'Credit entry for {customer} added successfully!')

    if not st.session_state.credit_books.empty:
        st.dataframe(st.session_state.credit_books)

# Quotation Builder Page
elif page == 'Quotation Builder':
    st.title('Quotation Builder')

    st.subheader('Select Items for Quotation')
    selected_items = st.multiselect('Select Items', st.session_state.inventory['Item'])

    if selected_items:
        selected_data = st.session_state.inventory[st.session_state.inventory['Item'].isin(selected_items)]
        st.write(selected_data)

        customer_name = st.text_input('Customer Name for Quotation')
        if st.button('Generate Quotation PDF'):
            if not customer_name:
                st.error('Please enter a customer name.')
            else:
                # Create PDF
                pdf_buffer = io.BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=letter)
                c.setFont('Helvetica', 12)

                c.drawString(30, 750, 'Quotation')
                c.drawString(30, 730, f'Customer: {customer_name}')
                c.drawString(30, 710, f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                c.drawString(30, 690, 'Items:')

                table_data = [['Item', 'Quantity', 'Unit Price (₹)', 'Total Price (₹)']]
                for _, row in selected_data.iterrows():
                    table_data.append([row['Item'], row['Quantity'], f'₹{row["Price"]:.2f}', f'₹{row["Quantity"] * row["Price"]:.2f}'])

                x_offset = 30
                y_offset = 670
                row_height = 20
                col_width = 150

                for row in table_data:
                    for col, cell in enumerate(row):
                        c.drawString(x_offset + col * col_width, y_offset, str(cell))
                    y_offset -= row_height

                c.showPage()
                c.save()
                pdf_buffer.seek(0)

                st.download_button(
                    label='Download Quotation PDF',
                    data=pdf_buffer,
                    file_name='quotation.pdf',
                    mime='application/pdf'
                )

# Sales Management Page
elif page == 'Sales Management':
    st.title('Sales Management')

    st.subheader('Add Sale')
    sale_customer = st.text_input('Customer Name')
    sale_item = st.selectbox('Item Sold', st.session_state.inventory['Item'])
    sale_quantity = st.number_input('Quantity Sold', min_value=1, step=1)
    sale_price = st.number_input('Price per Item (INR)', min_value=0.0, step=0.1)
    sale_date = st.date_input('Sale Date', datetime.now())

    if st.button('Add Sale'):
        if not sale_customer or not sale_item or sale_quantity <= 0 or sale_price < 0:
            st.error('Please fill in all fields.')
        else:
            new_sale = pd.DataFrame({'Customer': [sale_customer], 'Item': [sale_item], 'Quantity': [sale_quantity], 'Price': [sale_price], 'Date': [sale_date]})
            st.session_state.sales = pd.concat([st.session_state.sales, new_sale], ignore_index=True)
            # Update inventory
            st.session_state.inventory.loc[st.session_state.inventory['Item'] == sale_item, 'Quantity'] -= sale_quantity
            st.success(f'Sale to {sale_customer} added successfully!')

    st.subheader('Sales Records')
    if not st.session_state.sales.empty:
        st.dataframe(st.session_state.sales)
        
        # Sales analytics
        st.subheader('Sales Analytics')
        total_sales = st.session_state.sales['Quantity'] * st.session_state.sales['Price']
        st.write(f'Total Sales Revenue: ₹{total_sales.sum():.2f}')
        
        top_items = st.session_state.sales.groupby('Item').sum().sort_values(by='Quantity', ascending=False)
        st.bar_chart(top_items['Quantity'])

# Analytics Page
elif page == 'Analytics':
    st.title('Analytics')

    st.subheader('Category Distribution')
    category_counts = st.session_state.inventory['Category'].value_counts()
    st.bar_chart(category_counts)

    st.subheader('Sales Over Time')
    if not st.session_state.sales.empty:
        sales_over_time = st.session_state.sales.groupby('Date').sum()['Quantity']
        st.line_chart(sales_over_time)

    st.subheader('Top Customers')
    if not st.session_state.sales.empty:
        top_customers = st.session_state.sales.groupby('Customer').sum().sort_values(by='Quantity', ascending=False)
        st.bar_chart(top_customers['Quantity'])

    st.subheader('Credit Books Summary')
    if not st.session_state.credit_books.empty:
        total_credit = st.session_state.credit_books['Amount Due'].sum()
        st.write(f'Total Outstanding Credit: ₹{total_credit:.2f}')
        due_dates = st.session_state.credit_books.groupby('Due Date').sum()['Amount Due']
        st.line_chart(due_dates)

    st.subheader('Inventory Value by Category')
    inventory_value_by_category = st.session_state.inventory.groupby('Category').apply(lambda x: (x['Quantity'] * x['Price']).sum()).reset_index()
    inventory_value_by_category.columns = ['Category', 'Total Value']
    st.bar_chart(inventory_value_by_category.set_index('Category')['Total Value'])

    st.subheader('Low Stock Items')
    low_stock_items = st.session_state.inventory[st.session_state.inventory['Quantity'] < 10]
    if not low_stock_items.empty:
        st.warning('The following items are low in stock:')
        st.dataframe(low_stock_items)

    st.subheader('High Value Items')
    high_value_items = st.session_state.inventory[st.session_state.inventory['Price'] > 1000]
    if not high_value_items.empty:
        st.warning('The following items have a high unit price:')
        st.dataframe(high_value_items)
