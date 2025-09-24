import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, FlatList, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createStorefrontApiClient } from '@shopify/storefront-api-client';

import ProductCard from './ProductCard';

const client = createStorefrontApiClient({
  storeDomain: 'iwyyib-k6.myshopify.com',
  apiVersion: '2024-07', 
  publicAccessToken: '731502b536fef6d451f2a84ee51077a6', 
});

export default function App() {
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
          priceRange {
            minVariantPrice {
              amount
              currencyCode
            }
          }
          images(first: 1) {
            edges {
              node {
                url
                altText
              }
            }
          }
        }
      }
    }
  }
`;

      try {
        const response = await client.request(query);
        if (response && response.data && response.data.products) {
          setProducts(response.data.products.edges);
        } else {
          console.error('Failed to fetch products or response format is incorrect.');
        }
      } catch (error) {
        console.error('Error fetching products:', error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchProducts();
  }, []);

  if(isLoading){
    return(
           <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
      </View>
    )
  }


  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.header}>Trending Products</Text>
      <FlatList
        data={products}
        keyExtractor={(item) => item.node.id}
        renderItem={({ item }) => <ProductCard product={item} />}
        numColumns={2} 
        contentContainerStyle={styles.listContainer}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginVertical: 20,
  },
  listContainer: {
    paddingHorizontal: 8, 
  },
});