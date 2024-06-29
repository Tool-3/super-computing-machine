import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Initialize session state
if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame(columns=['Item', 'Quantity', 'Price', 'Supplier', 'Category'])

if 'credit_books' not in st.session_state:
    st.session_state.credit_books = pd.DataFrame(columns=['Customer', 'Amount Due', 'Due Date'])

# Title and branding
st.title('Stationery Shop Inventory Management System')
st.image('logo.png', width=200)

# Sidebar for adding items
st.sidebar.header('Add Item')
item = st.sidebar.text_input('Item Name')
quantity = st.sidebar.number_input('Quantity', min_value=0, step=1)
price = st.sidebar.number_input('Price (INR)', min_value=0.0, step=0.1)
supplier = st.sidebar.text_input('Supplier')
category = st.sidebar.selectbox('Category', ['Stationery', 'Office Supplies', 'Art Supplies'])

if st.sidebar.button('Add Item'):
    # Data validation
    if not item or not supplier or not category:
        st.sidebar.error('Please fill in all fields.')
    elif quantity < 0 or price < 0:
        st.sidebar.error('Quantity and price must be non-negative.')
    else:
        new_item = pd.DataFrame({'Item': [item], 'Quantity': [quantity], 'Price': [price], 'Supplier': [supplier], 'Category': [category]})
        st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
        st.sidebar.success(f'Item {item} added successfully!')

# Sidebar for removing items
st.sidebar.header('Remove Item')
if not st.session_state.inventory.empty:
    remove_item = st.sidebar.selectbox('Select Item to Remove', st.session_state.inventory['Item'])
    if st.sidebar.button('Remove Item'):
        st.session_state.inventory = st.session_state.inventory[st.session_state.inventory['Item'] != remove_item]
        st.sidebar.success(f'Item {remove_item} removed successfully!')
else:
    st.sidebar.write("No items to remove.")

# Main page for displaying inventory
st.header('Inventory')

# Search feature
search_term = st.text_input('Search Inventory')
filtered_inventory = st.session_state.inventory[st.session_state.inventory['Item'].str.contains(search_term, case=False, na=False)]

# Sorting and filtering
sort_by = st.selectbox('Sort By', ['Item', 'Quantity', 'Price', 'Supplier', 'Category'])
filter_by = st.selectbox('Filter By', ['All Categories'] + list(st.session_state.inventory['Category'].unique()))

if filter_by != 'All Categories':
    filtered_inventory = filtered_inventory[filtered_inventory['Category'] == filter_by]

filtered_inventory = filtered_inventory.sort_values(by=sort_by)

# Pagination
page_size = st.number_input('Page Size', min_value=1, step=1, value=10)
total_pages = (len(filtered_inventory) + page_size - 1) // page_size
page_number = st.number_input('Page Number', min_value=1, max_value=total_pages, step=1, value=1)
start_index = (page_number - 1) * page_size
end_index = start_index + page_size

st.dataframe(filtered_inventory.iloc[start_index:end_index])

# Detailed view of an item
if not filtered_inventory.empty:
    st.subheader('Detailed View')
    detailed_item = st.selectbox('Select Item to View Details', filtered_inventory['Item'])
    detailed_data = st.session_state.inventory[st.session_state.inventory['Item'] == detailed_item]
    st.write(detailed_data)

# Calculate total value
total_value = (filtered_inventory['Quantity'] * filtered_inventory['Price']).sum()
st.write(f'Total Inventory Value: ₹{total_value:.2f}')

# Low stock alerts
low_stock_items = filtered_inventory[filtered_inventory['Quantity'] < 10]
if not low_stock_items.empty:
    st.warning('The following items are low in stock:')
    st.dataframe(low_stock_items)

# Save to CSV
if st.button('Download Inventory as CSV'):
    csv = st.session_state.inventory.to_csv(index=False)
    st.download_button(label='Download CSV', data=csv, file_name='inventory.csv', mime='text/csv')

# Credit Books Section
st.header('Credit Books')

# Add credit entry
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

# Display credit books
if not st.session_state.credit_books.empty:
    st.dataframe(st.session_state.credit_books)

# Quotation Builder
st.header('Quotation Builder')

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
            c.drawString(30, 710, 'Items:')

            y = 690
            for _, row in selected_data.iterrows():
                c.drawString(30, y, f"{row['Item']} - Quantity: {row['Quantity']} - Price: ₹{row['Price']:.2f}")
                y -= 20

            c.save()
            pdf_buffer.seek(0)

            st.download_button(
                label='Download Quotation PDF',
                data=pdf_buffer,
                file_name='quotation.pdf',
                mime='application/pdf'
            )

# Charts and analytics
st.header('Analytics')
st.subheader('Category Distribution')
category_counts = st.session_state.inventory['Category'].value_counts()
st.bar_chart(category_counts)

st.subheader('Supplier Distribution')
supplier_counts = st.session_state.inventory['Supplier'].value_counts()
st.bar_chart(supplier_counts)

# Footer
st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        text-align: center;
        padding: 10px;
    }
    </style>
    <div class="footer">
        <p>&copy; 2024 Stationery Shop. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)
