import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Image, ActivityIndicator, Dimensions } from 'react-native';
import { client } from './shopifyClient'; // Import our shared client
import RenderHTML from 'react-native-render-html'; // Import the HTML renderer

const { width } = Dimensions.get('window');

export default function ProductDetailScreen({ route }) {
  const { productHandle } = route.params; // Get the handle passed from HomeScreen

  const [product, setProduct] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchProductByHandle() {
      // This is a new query to fetch ONE product using its handle
      const query = `
        query getProductByHandle($handle: String!) {
          product(handle: $handle) {
            id
            title
            descriptionHtml
            priceRange {
              minVariantPrice {
                amount
                currencyCode
              }
            }
            images(first: 5) {
              edges {
                node {
                  url
                  altText
                }
              }
            }
          }
        }
      `;

      const variables = { handle: productHandle };

      try {
        const response = await client.request(query, { variables });
        if (response.data.product) {
          setProduct(response.data.product);
        } else {
          // This is where a "Product not found" state would be set
          console.log('Product not found in API response.');
        }
      } catch (error) {
        console.error('Error fetching product:', error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchProductByHandle();
  }, [productHandle]); // Rerun if the handle changes

  if (isLoading) {
    return <ActivityIndicator style={styles.loader} size="large" />;
  }

  if (!product) {
    return (
      <View style={styles.loader}>
        <Text>Product not found.</Text>
      </View>
    );
  }

  const price = product.priceRange.minVariantPrice;

  return (
    <ScrollView style={styles.container}>
      <Image source={{ uri: product.images.edges[0].node.url }} style={styles.image} />
      <View style={styles.detailsContainer}>
        <Text style={styles.title}>{product.title}</Text>
        <Text style={styles.price}>{price.amount} {price.currencyCode}</Text>
        <Text style={styles.descriptionHeader}>Description</Text>
        <RenderHTML
          contentWidth={width}
          source={{ html: product.descriptionHtml }}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  loader: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    width: width,
    height: width, // Make the image square
  },
  detailsContainer: {
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  price: {
    fontSize: 20,
    fontWeight: '700',
    color: '#555',
    marginBottom: 16,
  },
  descriptionHeader: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
});