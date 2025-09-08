// Admin Panel JavaScript Functions

function refreshData() {
    location.reload();
}

function addProduct() {
    const form = document.getElementById('addProductForm');
    const formData = new FormData(form);
    
    const productData = {
        name: document.getElementById('productName').value,
        description: document.getElementById('productDescription').value,
        price: parseFloat(document.getElementById('productPrice').value),
        category: document.getElementById('productCategory').value,
        image_url: document.getElementById('productImageUrl').value,
        stock: parseInt(document.getElementById('productStock').value)
    };
    
    // Validate required fields
    if (!productData.name || !productData.description || !productData.price || !productData.category) {
        alert('Please fill in all required fields');
        return;
    }
    
    fetch('/api/products', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(productData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error adding product: ' + data.error);
        } else {
            // Close modal and refresh page
            bootstrap.Modal.getInstance(document.getElementById('addProductModal')).hide();
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding product');
    });
}

function editProduct(productId) {
    // Find product data from the table
    const row = document.querySelector(`tr[data-product-id="${productId}"]`);
    if (!row) {
        alert('Product not found');
        return;
    }
    
    // Get current product data
    fetch('/api/products')
    .then(response => response.json())
    .then(products => {
        const product = products.find(p => p.id === productId);
        if (!product) {
            alert('Product not found');
            return;
        }
        
        // Populate edit form
        document.getElementById('editProductId').value = product.id;
        document.getElementById('editProductName').value = product.name;
        document.getElementById('editProductDescription').value = product.description;
        document.getElementById('editProductPrice').value = product.price;
        document.getElementById('editProductCategory').value = product.category;
        document.getElementById('editProductImageUrl').value = product.image_url || '';
        document.getElementById('editProductStock').value = product.stock;
        
        // Show modal
        new bootstrap.Modal(document.getElementById('editProductModal')).show();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error loading product data');
    });
}

function updateProduct() {
    const productId = document.getElementById('editProductId').value;
    
    const productData = {
        name: document.getElementById('editProductName').value,
        description: document.getElementById('editProductDescription').value,
        price: parseFloat(document.getElementById('editProductPrice').value),
        category: document.getElementById('editProductCategory').value,
        image_url: document.getElementById('editProductImageUrl').value,
        stock: parseInt(document.getElementById('editProductStock').value)
    };
    
    // Validate required fields
    if (!productData.name || !productData.description || !productData.price || !productData.category) {
        alert('Please fill in all required fields');
        return;
    }
    
    fetch(`/api/products/${productId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(productData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error updating product: ' + data.error);
        } else {
            // Close modal and refresh page
            bootstrap.Modal.getInstance(document.getElementById('editProductModal')).hide();
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating product');
    });
}

function deleteProduct(productId) {
    if (!confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
        return;
    }
    
    fetch(`/api/products/${productId}`, {
        method: 'DELETE',
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error deleting product: ' + data.error);
        } else {
            // Remove row from table and refresh
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error deleting product');
    });
}

// Initialize form validation
document.addEventListener('DOMContentLoaded', function() {
    // Add form validation for number inputs
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.value < 0) {
                this.value = 0;
            }
        });
    });
    
    // Clear form when add modal is closed
    const addModal = document.getElementById('addProductModal');
    if (addModal) {
        addModal.addEventListener('hidden.bs.modal', function() {
            document.getElementById('addProductForm').reset();
        });
    }
});
