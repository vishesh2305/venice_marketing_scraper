import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, FlatList, ActivityIndicator, TouchableOpacity } from 'react-native';
import ProductCard from './ProductCard';
import {client} from "./shopifyClient";


// We now receive 'navigation' as a prop
export default function HomeScreen({ navigation }) {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

useEffect(() => {
  async function fetchProducts() {
    const query = `
      {
        products(first: 10) {
          edges {
            node {
              id
              title
              handle
              priceRange { minVariantPrice { amount currencyCode } }
              images(first: 1) { edges { node { url altText } } }
            }
          }
        }
      }
    `;
    try {
      const response = await client.request(query);
      console.log("Api Response: ", response);
if (response && response.data && response.data.products) {
  
  setProducts(response.data.products.edges);
}

    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setIsLoading(false);
    }
  }

  fetchProducts();
}, []);


  if (isLoading) {
    return <View style={styles.loadingContainer}><ActivityIndicator size="large" /></View>;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Trending Products</Text>
      <FlatList
        data={products}
        keyExtractor={(item) => item.node.id}
        renderItem={({ item }) => (
          // Make the card tappable
          <TouchableOpacity onPress={() => navigation.navigate('ProductDetail', { productHandle: item.node.handle })}>
            <ProductCard product={item} />
          </TouchableOpacity>
        )}
        numColumns={2}
        contentContainerStyle={styles.listContainer}
      />
    </View>
  );
}

const styles = StyleSheet.create({
    // ... (All the styles from your old App.js can be pasted here)
    loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    header: { fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginVertical: 20 },
    listContainer: { paddingHorizontal: 8 },
});