import React from 'react';
import { StyleSheet, Text, View, Image, Dimensions } from 'react-native';

const { width } = Dimensions.get('window');
const cardWidth = width / 2 - 24; 

export default function ProductCard({ product }) {
  const { title, priceRange, images } = product.node;
  const price = priceRange.minVariantPrice.amount;
  const imageUrl = images.edges[0]?.node.url;

  return (
    <View style={styles.card}>
      {imageUrl ? (
        <Image source={{ uri: imageUrl }} style={styles.image} />
      ) : (
        <View style={[styles.image, styles.imagePlaceholder]} />
      )}
      <Text style={styles.title} numberOfLines={2}>
        {title}
      </Text>
      <Text style={styles.price}>
        {price} {priceRange.minVariantPrice.currencyCode}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: cardWidth,
    backgroundColor: '#ffffff',
    borderRadius: 8,
    margin: 8,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    overflow: 'hidden', 
  },
  image: {
    width: '100%',
    height: 160,
  },
  imagePlaceholder: {
    backgroundColor: '#e0e0e0',
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    paddingHorizontal: 8,
    paddingTop: 8,
    minHeight: 40, 
  },
  price: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2b2b2b',
    paddingHorizontal: 8,
    paddingBottom: 12,
  },
});