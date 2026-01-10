# SJSU RideShare Development Guide
## Section 11: React Native Mobile App - Part 2

**Version:** 1.0  
**Duration:** Week 11  
**Focus:** Ride posting, bookings, maps, real-time tracking, push notifications

---

# SECTION 11: React Native Mobile App - Part 2

## Learning Objectives
- Implement ride posting functionality
- Build booking flow
- Integrate Google Maps
- Implement real-time location tracking with WebSocket
- Set up push notifications with Firebase
- Handle location permissions
- Build driver dashboard
- Implement payment UI with Stripe

## Technologies
- React Native Maps
- WebSocket for real-time tracking
- Expo Location
- Firebase Cloud Messaging (FCM)
- Stripe React Native SDK
- React Native Geolocation

## Prerequisites
- Section 10 completed ✅
- Backend APIs operational
- Firebase project set up
- Stripe account configured
- Understanding of WebSocket

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - React Native Mobile App (Part 2)

CONTEXT:
Section 10 completed. Basic app with auth and home screen working.
Adding advanced features: ride posting, bookings, maps, tracking, notifications.
Section 11 of 13.

GOAL:
Complete mobile app with:
- Post ride functionality
- Booking flow with payment
- Google Maps integration
- Real-time location tracking
- Push notifications
- Driver dashboard
- My rides management

DETAILED REQUIREMENTS:

1. ADDITIONAL DEPENDENCIES:

   ```bash
   npm install react-native-maps
   npm install expo-location
   npm install expo-notifications
   npm install @stripe/stripe-react-native
   npm install react-native-webview
   npm install date-fns
   npm install react-native-modal
   npm install react-native-gesture-handler
   ```

2. POST RIDE SCREEN (src/screens/rides/PostRideScreen.js):

   ```javascript
   import React, { useState } from 'react';
   import {
     View,
     Text,
     ScrollView,
     StyleSheet,
     TouchableOpacity,
     Platform,
     Alert
   } from 'react-native';
   import DateTimePicker from '@react-native-community/datetimepicker';
   import * as Location from 'expo-location';
   import Input from '../../components/common/Input';
   import Button from '../../components/common/Button';
   import LocationPicker from '../../components/LocationPicker';
   import * as ridesApi from '../../api/rides';
   import { COLORS } from '../../constants/colors';
   
   export default function PostRideScreen({ navigation }) {
     const [formData, setFormData] = useState({
       origin: null,
       destination: null,
       departureTime: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
       availableSeats: 3,
       pricePerSeat: 10,
       vehicleMake: '',
       vehicleModel: '',
       vehicleYear: '',
       vehicleLicensePlate: '',
       vehicleColor: '',
       preferences: {
         music: true,
         ac: true,
         stops: false,
         pets: false,
         smoking: false
       },
       notes: ''
     });
     
     const [showDatePicker, setShowDatePicker] = useState(false);
     const [showTimePicker, setShowTimePicker] = useState(false);
     const [loading, setLoading] = useState(false);
     
     const handleLocationSelect = (type, location) => {
       setFormData(prev => ({
         ...prev,
         [type]: location
       }));
     };
     
     const validateForm = () => {
       if (!formData.origin) {
         Alert.alert('Error', 'Please select origin location');
         return false;
       }
       if (!formData.destination) {
         Alert.alert('Error', 'Please select destination location');
         return false;
       }
       if (formData.departureTime < new Date()) {
         Alert.alert('Error', 'Departure time must be in the future');
         return false;
       }
       if (!formData.vehicleMake || !formData.vehicleModel) {
         Alert.alert('Error', 'Please enter vehicle information');
         return false;
       }
       return true;
     };
     
     const handlePostRide = async () => {
       if (!validateForm()) return;
       
       setLoading(true);
       try {
         const rideData = {
           origin: {
             address: formData.origin.address,
             lat: formData.origin.lat,
             lng: formData.origin.lng
           },
           destination: {
             address: formData.destination.address,
             lat: formData.destination.lat,
             lng: formData.destination.lng
           },
           departure_time: formData.departureTime.toISOString(),
           available_seats: formData.availableSeats,
           price_per_seat: formData.pricePerSeat,
           vehicle: {
             make: formData.vehicleMake,
             model: formData.vehicleModel,
             year: parseInt(formData.vehicleYear),
             license_plate: formData.vehicleLicensePlate,
             color: formData.vehicleColor
           },
           preferences: formData.preferences,
           notes: formData.notes
         };
         
         await ridesApi.postRide(rideData);
         Alert.alert('Success', 'Ride posted successfully!', [
           { text: 'OK', onPress: () => navigation.goBack() }
         ]);
       } catch (error) {
         Alert.alert('Error', error.response?.data?.detail || 'Failed to post ride');
       } finally {
         setLoading(false);
       }
     };
     
     return (
       <ScrollView style={styles.container}>
         <View style={styles.content}>
           <Text style={styles.sectionTitle}>Route</Text>
           
           <LocationPicker
             label="Pickup Location"
             location={formData.origin}
             onLocationSelect={(loc) => handleLocationSelect('origin', loc)}
           />
           
           <LocationPicker
             label="Destination"
             location={formData.destination}
             onLocationSelect={(loc) => handleLocationSelect('destination', loc)}
           />
           
           <Text style={styles.sectionTitle}>Date & Time</Text>
           
           <TouchableOpacity
             style={styles.dateTimeButton}
             onPress={() => setShowDatePicker(true)}
           >
             <Text>{formData.departureTime.toLocaleDateString()}</Text>
           </TouchableOpacity>
           
           <TouchableOpacity
             style={styles.dateTimeButton}
             onPress={() => setShowTimePicker(true)}
           >
             <Text>{formData.departureTime.toLocaleTimeString()}</Text>
           </TouchableOpacity>
           
           {showDatePicker && (
             <DateTimePicker
               value={formData.departureTime}
               mode="date"
               onChange={(event, date) => {
                 setShowDatePicker(false);
                 if (date) setFormData(prev => ({ ...prev, departureTime: date }));
               }}
             />
           )}
           
           {showTimePicker && (
             <DateTimePicker
               value={formData.departureTime}
               mode="time"
               onChange={(event, date) => {
                 setShowTimePicker(false);
                 if (date) setFormData(prev => ({ ...prev, departureTime: date }));
               }}
             />
           )}
           
           <Text style={styles.sectionTitle}>Ride Details</Text>
           
           <View style={styles.row}>
             <View style={styles.halfInput}>
               <Text style={styles.label}>Available Seats</Text>
               <Input
                 value={formData.availableSeats.toString()}
                 onChangeText={(val) => setFormData(prev => ({
                   ...prev,
                   availableSeats: parseInt(val) || 1
                 }))}
                 keyboardType="number-pad"
               />
             </View>
             
             <View style={styles.halfInput}>
               <Text style={styles.label}>Price per Seat ($)</Text>
               <Input
                 value={formData.pricePerSeat.toString()}
                 onChangeText={(val) => setFormData(prev => ({
                   ...prev,
                   pricePerSeat: parseFloat(val) || 0
                 }))}
                 keyboardType="decimal-pad"
               />
             </View>
           </View>
           
           <Text style={styles.sectionTitle}>Vehicle Information</Text>
           
           <Input
             placeholder="Make (e.g., Toyota)"
             value={formData.vehicleMake}
             onChangeText={(val) => setFormData(prev => ({ ...prev, vehicleMake: val }))}
           />
           
           <Input
             placeholder="Model (e.g., Camry)"
             value={formData.vehicleModel}
             onChangeText={(val) => setFormData(prev => ({ ...prev, vehicleModel: val }))}
           />
           
           <View style={styles.row}>
             <View style={styles.halfInput}>
               <Input
                 placeholder="Year"
                 value={formData.vehicleYear}
                 onChangeText={(val) => setFormData(prev => ({ ...prev, vehicleYear: val }))}
                 keyboardType="number-pad"
               />
             </View>
             
             <View style={styles.halfInput}>
               <Input
                 placeholder="Color"
                 value={formData.vehicleColor}
                 onChangeText={(val) => setFormData(prev => ({ ...prev, vehicleColor: val }))}
               />
             </View>
           </View>
           
           <Input
             placeholder="License Plate"
             value={formData.vehicleLicensePlate}
             onChangeText={(val) => setFormData(prev => ({
               ...prev,
               vehicleLicensePlate: val.toUpperCase()
             }))}
             autoCapitalize="characters"
           />
           
           <Text style={styles.sectionTitle}>Preferences</Text>
           
           {Object.entries(formData.preferences).map(([key, value]) => (
             <TouchableOpacity
               key={key}
               style={styles.preferenceRow}
               onPress={() => setFormData(prev => ({
                 ...prev,
                 preferences: {
                   ...prev.preferences,
                   [key]: !value
                 }
               }))}
             >
               <Text style={styles.preferenceLabel}>
                 {key.charAt(0).toUpperCase() + key.slice(1)}
               </Text>
               <View style={[styles.checkbox, value && styles.checkboxActive]} />
             </TouchableOpacity>
           ))}
           
           <Text style={styles.sectionTitle}>Additional Notes</Text>
           
           <Input
             placeholder="Any additional information..."
             value={formData.notes}
             onChangeText={(val) => setFormData(prev => ({ ...prev, notes: val }))}
             multiline
             numberOfLines={4}
             style={styles.notesInput}
           />
           
           <Button
             title="Post Ride"
             onPress={handlePostRide}
             loading={loading}
             style={styles.submitButton}
           />
         </View>
       </ScrollView>
     );
   }
   
   const styles = StyleSheet.create({
     container: {
       flex: 1,
       backgroundColor: COLORS.background,
     },
     content: {
       padding: 16,
     },
     sectionTitle: {
       fontSize: 18,
       fontWeight: '600',
       color: COLORS.text,
       marginTop: 16,
       marginBottom: 12,
     },
     row: {
       flexDirection: 'row',
       justifyContent: 'space-between',
     },
     halfInput: {
       flex: 1,
       marginHorizontal: 4,
     },
     label: {
       fontSize: 14,
       color: COLORS.gray,
       marginBottom: 4,
     },
     dateTimeButton: {
       backgroundColor: COLORS.white,
       padding: 16,
       borderRadius: 8,
       borderWidth: 1,
       borderColor: COLORS.border,
       marginBottom: 12,
     },
     preferenceRow: {
       flexDirection: 'row',
       justifyContent: 'space-between',
       alignItems: 'center',
       paddingVertical: 12,
       borderBottomWidth: 1,
       borderBottomColor: COLORS.border,
     },
     preferenceLabel: {
       fontSize: 16,
       color: COLORS.text,
     },
     checkbox: {
       width: 24,
       height: 24,
       borderRadius: 4,
       borderWidth: 2,
       borderColor: COLORS.gray,
     },
     checkboxActive: {
       backgroundColor: COLORS.primary,
       borderColor: COLORS.primary,
     },
     notesInput: {
       height: 100,
       textAlignVertical: 'top',
     },
     submitButton: {
       marginTop: 24,
       marginBottom: 40,
     },
   });
   ```

3. LOCATION PICKER COMPONENT (src/components/LocationPicker.js):

   ```javascript
   import React, { useState } from 'react';
   import {
     View,
     Text,
     TouchableOpacity,
     StyleSheet,
     Modal,
     TextInput,
     FlatList,
     ActivityIndicator
   } from 'react-native';
   import MapView, { Marker } from 'react-native-maps';
   import * as Location from 'expo-location';
   import * as mapsApi from '../api/maps';
   import { COLORS } from '../constants/colors';
   
   export default function LocationPicker({ label, location, onLocationSelect }) {
     const [modalVisible, setModalVisible] = useState(false);
     const [searchQuery, setSearchQuery] = useState('');
     const [suggestions, setSuggestions] = useState([]);
     const [loading, setLoading] = useState(false);
     const [selectedLocation, setSelectedLocation] = useState(location);
     
     const handleSearchChange = async (text) => {
       setSearchQuery(text);
       
       if (text.length < 3) {
         setSuggestions([]);
         return;
       }
       
       setLoading(true);
       try {
         const response = await mapsApi.autocompletePlaces(text);
         setSuggestions(response.data.predictions);
       } catch (error) {
         console.error('Autocomplete error:', error);
       } finally {
         setLoading(false);
       }
     };
     
     const handleSuggestionSelect = async (placeId) => {
       try {
         const response = await mapsApi.getPlaceDetails(placeId);
         const place = response.data;
         
         setSelectedLocation({
           address: place.formatted_address,
           lat: place.geometry.location.lat,
           lng: place.geometry.location.lng
         });
         setSuggestions([]);
         setSearchQuery(place.formatted_address);
       } catch (error) {
         console.error('Place details error:', error);
       }
     };
     
     const handleCurrentLocation = async () => {
       try {
         const { status } = await Location.requestForegroundPermissionsAsync();
         if (status !== 'granted') {
           Alert.alert('Permission denied', 'Location permission is required');
           return;
         }
         
         const location = await Location.getCurrentPositionAsync({});
         const response = await mapsApi.reverseGeocode(
           location.coords.latitude,
           location.coords.longitude
         );
         
         setSelectedLocation({
           address: response.data.formatted_address,
           lat: location.coords.latitude,
           lng: location.coords.longitude
         });
         setSearchQuery(response.data.formatted_address);
       } catch (error) {
         console.error('Current location error:', error);
       }
     };
     
     const handleConfirm = () => {
       onLocationSelect(selectedLocation);
       setModalVisible(false);
     };
     
     return (
       <View style={styles.container}>
         <Text style={styles.label}>{label}</Text>
         <TouchableOpacity
           style={styles.input}
           onPress={() => setModalVisible(true)}
         >
           <Text style={location ? styles.text : styles.placeholder}>
             {location ? location.address : `Select ${label.toLowerCase()}`}
           </Text>
         </TouchableOpacity>
         
         <Modal
           visible={modalVisible}
           animationType="slide"
           onRequestClose={() => setModalVisible(false)}
         >
           <View style={styles.modal}>
             <View style={styles.header}>
               <TouchableOpacity onPress={() => setModalVisible(false)}>
                 <Text style={styles.cancelButton}>Cancel</Text>
               </TouchableOpacity>
               <Text style={styles.headerTitle}>{label}</Text>
               <TouchableOpacity
                 onPress={handleConfirm}
                 disabled={!selectedLocation}
               >
                 <Text
                   style={[
                     styles.confirmButton,
                     !selectedLocation && styles.confirmButtonDisabled
                   ]}
                 >
                   Confirm
                 </Text>
               </TouchableOpacity>
             </View>
             
             <View style={styles.searchContainer}>
               <TextInput
                 style={styles.searchInput}
                 placeholder="Search for a place..."
                 value={searchQuery}
                 onChangeText={handleSearchChange}
                 autoFocus
               />
               <TouchableOpacity
                 style={styles.currentLocationButton}
                 onPress={handleCurrentLocation}
               >
                 <Text style={styles.currentLocationText}>Use Current Location</Text>
               </TouchableOpacity>
             </View>
             
             {loading && (
               <View style={styles.loadingContainer}>
                 <ActivityIndicator size="small" color={COLORS.primary} />
               </View>
             )}
             
             {suggestions.length > 0 && (
               <FlatList
                 data={suggestions}
                 keyExtractor={(item) => item.place_id}
                 renderItem={({ item }) => (
                   <TouchableOpacity
                     style={styles.suggestion}
                     onPress={() => handleSuggestionSelect(item.place_id)}
                   >
                     <Text style={styles.suggestionText}>{item.description}</Text>
                   </TouchableOpacity>
                 )}
                 style={styles.suggestionsList}
               />
             )}
             
             {selectedLocation && (
               <MapView
                 style={styles.map}
                 initialRegion={{
                   latitude: selectedLocation.lat,
                   longitude: selectedLocation.lng,
                   latitudeDelta: 0.01,
                   longitudeDelta: 0.01,
                 }}
               >
                 <Marker
                   coordinate={{
                     latitude: selectedLocation.lat,
                     longitude: selectedLocation.lng,
                   }}
                 />
               </MapView>
             )}
           </View>
         </Modal>
       </View>
     );
   }
   
   const styles = StyleSheet.create({
     container: {
       marginBottom: 16,
     },
     label: {
       fontSize: 14,
       fontWeight: '500',
       color: COLORS.text,
       marginBottom: 8,
     },
     input: {
       backgroundColor: COLORS.white,
       padding: 16,
       borderRadius: 8,
       borderWidth: 1,
       borderColor: COLORS.border,
     },
     text: {
       fontSize: 16,
       color: COLORS.text,
     },
     placeholder: {
       fontSize: 16,
       color: COLORS.placeholder,
     },
     modal: {
       flex: 1,
       backgroundColor: COLORS.white,
     },
     header: {
       flexDirection: 'row',
       justifyContent: 'space-between',
       alignItems: 'center',
       padding: 16,
       borderBottomWidth: 1,
       borderBottomColor: COLORS.border,
     },
     cancelButton: {
       color: COLORS.danger,
       fontSize: 16,
     },
     headerTitle: {
       fontSize: 18,
       fontWeight: '600',
       color: COLORS.text,
     },
     confirmButton: {
       color: COLORS.primary,
       fontSize: 16,
       fontWeight: '600',
     },
     confirmButtonDisabled: {
       color: COLORS.gray,
     },
     searchContainer: {
       padding: 16,
     },
     searchInput: {
       backgroundColor: COLORS.lightGray,
       padding: 12,
       borderRadius: 8,
       fontSize: 16,
     },
     currentLocationButton: {
       marginTop: 12,
       padding: 12,
       backgroundColor: COLORS.primary,
       borderRadius: 8,
       alignItems: 'center',
     },
     currentLocationText: {
       color: COLORS.white,
       fontSize: 16,
       fontWeight: '600',
     },
     loadingContainer: {
       padding: 16,
       alignItems: 'center',
     },
     suggestionsList: {
       maxHeight: 300,
     },
     suggestion: {
       padding: 16,
       borderBottomWidth: 1,
       borderBottomColor: COLORS.border,
     },
     suggestionText: {
       fontSize: 16,
       color: COLORS.text,
     },
     map: {
       flex: 1,
     },
   });
   ```

4. BOOKING SCREEN (src/screens/bookings/BookingScreen.js):

   ```javascript
   import React, { useState } from 'react';
   import {
     View,
     Text,
     ScrollView,
     StyleSheet,
     Alert
   } from 'react-native';
   import { StripeProvider, CardField, useStripe } from '@stripe/stripe-react-native';
   import Button from '../../components/common/Button';
   import LocationPicker from '../../components/LocationPicker';
   import * as bookingsApi from '../../api/bookings';
   import * as paymentsApi from '../../api/payments';
   import { COLORS } from '../../constants/colors';
   import { STRIPE_PUBLISHABLE_KEY } from '../../constants/api';
   
   function BookingForm({ route, navigation }) {
     const { ride } = route.params;
     const { confirmPayment } = useStripe();
     const [seats, setSeats] = useState(1);
     const [pickupLocation, setPickupLocation] = useState(null);
     const [dropoffLocation, setDropoffLocation] = useState(null);
     const [notes, setNotes] = useState('');
     const [loading, setLoading] = useState(false);
     const [cardComplete, setCardComplete] = useState(false);
     
     const totalPrice = seats * ride.price_per_seat;
     
     const handleBooking = async () => {
       if (!pickupLocation || !dropoffLocation) {
         Alert.alert('Error', 'Please select pickup and dropoff locations');
         return;
       }
       
       if (!cardComplete) {
         Alert.alert('Error', 'Please enter valid card details');
         return;
       }
       
       setLoading(true);
       
       try {
         // 1. Create booking
         const bookingResponse = await bookingsApi.createBooking({
           ride_id: ride.id,
           seats_booked: seats,
           pickup_location: pickupLocation,
           dropoff_location: dropoffLocation,
           passenger_notes: notes
         });
         
         const booking = bookingResponse.data;
         
         // 2. Create payment intent
         const paymentResponse = await paymentsApi.createPaymentIntent(
           booking.id
         );
         
         // 3. Confirm payment with Stripe
         const { error } = await confirmPayment(
           paymentResponse.data.client_secret,
           {
             paymentMethodType: 'Card',
           }
         );
         
         if (error) {
           Alert.alert('Payment Failed', error.message);
           return;
         }
         
         Alert.alert(
           'Booking Requested!',
           'Your booking request has been sent to the driver. You will be notified once approved.',
           [{ text: 'OK', onPress: () => navigation.navigate('MyRides') }]
         );
       } catch (error) {
         Alert.alert(
           'Error',
           error.response?.data?.detail || 'Booking failed'
         );
       } finally {
         setLoading(false);
       }
     };
     
     return (
       <ScrollView style={styles.container}>
         <View style={styles.content}>
           <View style={styles.rideInfo}>
             <Text style={styles.route}>
               {ride.origin.address} → {ride.destination.address}
             </Text>
             <Text style={styles.price}>
               ${ride.price_per_seat} per seat
             </Text>
           </View>
           
           <Text style={styles.sectionTitle}>Number of Seats</Text>
           <View style={styles.seatsContainer}>
             {[1, 2, 3, 4].map((num) => (
               <TouchableOpacity
                 key={num}
                 style={[
                   styles.seatButton,
                   seats === num && styles.seatButtonActive
                 ]}
                 onPress={() => setSeats(num)}
                 disabled={num > ride.available_seats}
               >
                 <Text
                   style={[
                     styles.seatButtonText,
                     seats === num && styles.seatButtonTextActive
                   ]}
                 >
                   {num}
                 </Text>
               </TouchableOpacity>
             ))}
           </View>
           
           <LocationPicker
             label="Pickup Location"
             location={pickupLocation}
             onLocationSelect={setPickupLocation}
           />
           
           <LocationPicker
             label="Dropoff Location"
             location={dropoffLocation}
             onLocationSelect={setDropoffLocation}
           />
           
           <Text style={styles.sectionTitle}>Payment Method</Text>
           <CardField
             postalCodeEnabled={false}
             style={styles.cardField}
             onCardChange={(cardDetails) => {
               setCardComplete(cardDetails.complete);
             }}
           />
           
           <View style={styles.totalContainer}>
             <Text style={styles.totalLabel}>Total</Text>
             <Text style={styles.totalAmount}>${totalPrice.toFixed(2)}</Text>
           </View>
           
           <Button
             title={`Book for $${totalPrice.toFixed(2)}`}
             onPress={handleBooking}
             loading={loading}
             disabled={!cardComplete}
             style={styles.bookButton}
           />
         </View>
       </ScrollView>
     );
   }
   
   export default function BookingScreen(props) {
     return (
       <StripeProvider publishableKey={STRIPE_PUBLISHABLE_KEY}>
         <BookingForm {...props} />
       </StripeProvider>
     );
   }
   
   const styles = StyleSheet.create({
     container: {
       flex: 1,
       backgroundColor: COLORS.background,
     },
     content: {
       padding: 16,
     },
     rideInfo: {
       backgroundColor: COLORS.white,
       padding: 16,
       borderRadius: 8,
       marginBottom: 24,
     },
     route: {
       fontSize: 16,
       color: COLORS.text,
       marginBottom: 8,
     },
     price: {
       fontSize: 20,
       fontWeight: 'bold',
       color: COLORS.primary,
     },
     sectionTitle: {
       fontSize: 16,
       fontWeight: '600',
       color: COLORS.text,
       marginBottom: 12,
     },
     seatsContainer: {
       flexDirection: 'row',
       justifyContent: 'space-around',
       marginBottom: 24,
     },
     seatButton: {
       width: 60,
       height: 60,
       borderRadius: 30,
       borderWidth: 2,
       borderColor: COLORS.primary,
       alignItems: 'center',
       justifyContent: 'center',
     },
     seatButtonActive: {
       backgroundColor: COLORS.primary,
     },
     seatButtonText: {
       fontSize: 20,
       fontWeight: '600',
       color: COLORS.primary,
     },
     seatButtonTextActive: {
       color: COLORS.white,
     },
     cardField: {
       height: 50,
       marginBottom: 24,
     },
     totalContainer: {
       flexDirection: 'row',
       justifyContent: 'space-between',
       padding: 16,
       backgroundColor: COLORS.white,
       borderRadius: 8,
       marginBottom: 24,
     },
     totalLabel: {
       fontSize: 18,
       fontWeight: '600',
       color: COLORS.text,
     },
     totalAmount: {
       fontSize: 24,
       fontWeight: 'bold',
       color: COLORS.primary,
     },
     bookButton: {
       marginBottom: 40,
     },
   });
   ```

5. REAL-TIME TRACKING SCREEN (src/screens/tracking/TrackingScreen.js):

   ```javascript
   import React, { useState, useEffect, useRef } from 'react';
   import { View, Text, StyleSheet, Alert } from 'react-native';
   import MapView, { Marker, Polyline } from 'react-native-maps';
   import * as Location from 'expo-location';
   import { useAuth } from '../../hooks/useAuth';
   import { COLORS } from '../../constants/colors';
   import { WS_BASE_URL } from '../../constants/api';
   
   export default function TrackingScreen({ route }) {
     const { booking, isDriver } = route.params;
     const { user } = useAuth();
     const [driverLocation, setDriverLocation] = useState(null);
     const [eta, setEta] = useState(null);
     const ws = useRef(null);
     const mapRef = useRef(null);
     
     useEffect(() => {
       connectWebSocket();
       
       if (isDriver) {
         startLocationTracking();
       }
       
       return () => {
         if (ws.current) {
           ws.current.close();
         }
       };
     }, []);
     
     const connectWebSocket = async () => {
       try {
         const token = await AsyncStorage.getItem('accessToken');
         const endpoint = isDriver
           ? `${WS_BASE_URL}/tracking/ride/${booking.ride_id}/driver?token=${token}`
           : `${WS_BASE_URL}/tracking/ride/${booking.ride_id}/passenger?token=${token}`;
         
         ws.current = new WebSocket(endpoint);
         
         ws.current.onopen = () => {
           console.log('WebSocket connected');
         };
         
         ws.current.onmessage = (event) => {
           const data = JSON.parse(event.data);
           
           if (data.type === 'location_update') {
             setDriverLocation({
               latitude: data.lat,
               longitude: data.lng,
               speed: data.speed,
               bearing: data.bearing
             });
             setEta(data.eta_seconds);
             
             // Center map on driver location
             if (mapRef.current) {
               mapRef.current.animateToRegion({
                 latitude: data.lat,
                 longitude: data.lng,
                 latitudeDelta: 0.01,
                 longitudeDelta: 0.01,
               });
             }
           }
         };
         
         ws.current.onerror = (error) => {
           console.error('WebSocket error:', error);
           Alert.alert('Connection Error', 'Failed to connect to tracking service');
         };
         
         ws.current.onclose = () => {
           console.log('WebSocket closed');
         };
       } catch (error) {
         console.error('WebSocket connection error:', error);
       }
     };
     
     const startLocationTracking = async () => {
       const { status } = await Location.requestForegroundPermissionsAsync();
       if (status !== 'granted') {
         Alert.alert('Permission Required', 'Location permission is required for tracking');
         return;
       }
       
       // Send location updates every 5 seconds
       const subscription = await Location.watchPositionAsync(
         {
           accuracy: Location.Accuracy.BestForNavigation,
           timeInterval: 5000,
           distanceInterval: 10,
         },
         (location) => {
           if (ws.current && ws.current.readyState === WebSocket.OPEN) {
             ws.current.send(JSON.stringify({
               lat: location.coords.latitude,
               lng: location.coords.longitude,
               speed: location.coords.speed * 3.6, // m/s to km/h
               bearing: location.coords.heading,
               accuracy: location.coords.accuracy,
               timestamp: new Date().toISOString()
             }));
           }
         }
       );
       
       return () => subscription.remove();
     };
     
     const formatETA = (seconds) => {
       if (!seconds) return 'Calculating...';
       const minutes = Math.round(seconds / 60);
       return `${minutes} min`;
     };
     
     return (
       <View style={styles.container}>
         <MapView
           ref={mapRef}
           style={styles.map}
           initialRegion={{
             latitude: booking.pickup_location.lat,
             longitude: booking.pickup_location.lng,
             latitudeDelta: 0.05,
             longitudeDelta: 0.05,
           }}
         >
           {driverLocation && (
             <Marker
               coordinate={driverLocation}
               title="Driver"
               description="Current location"
             >
               <View style={styles.driverMarker}>
                 <Text style={styles.driverMarkerText}>🚗</Text>
               </View>
             </Marker>
           )}
           
           <Marker
             coordinate={{
               latitude: booking.pickup_location.lat,
               longitude: booking.pickup_location.lng,
             }}
             title="Pickup"
             pinColor={COLORS.primary}
           />
           
           <Marker
             coordinate={{
               latitude: booking.dropoff_location.lat,
               longitude: booking.dropoff_location.lng,
             }}
             title="Dropoff"
             pinColor={COLORS.success}
           />
         </MapView>
         
         <View style={styles.etaContainer}>
           <Text style={styles.etaLabel}>ETA</Text>
           <Text style={styles.etaValue}>{formatETA(eta)}</Text>
         </View>
       </View>
     );
   }
   
   const styles = StyleSheet.create({
     container: {
       flex: 1,
     },
     map: {
       flex: 1,
     },
     driverMarker: {
       backgroundColor: COLORS.primary,
       padding: 8,
       borderRadius: 20,
     },
     driverMarkerText: {
       fontSize: 20,
     },
     etaContainer: {
       position: 'absolute',
       top: 20,
       left: 20,
       right: 20,
       backgroundColor: COLORS.white,
       padding: 16,
       borderRadius: 12,
       shadowColor: '#000',
       shadowOffset: { width: 0, height: 2 },
       shadowOpacity: 0.2,
       shadowRadius: 4,
       elevation: 5,
       flexDirection: 'row',
       justifyContent: 'space-between',
       alignItems: 'center',
     },
     etaLabel: {
       fontSize: 16,
       color: COLORS.gray,
     },
     etaValue: {
       fontSize: 24,
       fontWeight: 'bold',
       color: COLORS.primary,
     },
   });
   ```

6. PUSH NOTIFICATIONS SETUP (src/utils/notifications.js):

   ```javascript
   import * as Notifications from 'expo-notifications';
   import * as Device from 'expo-device';
   import { Platform } from 'react-native';
   import * as usersApi from '../api/users';
   
   // Configure how notifications are displayed
   Notifications.setNotificationHandler({
     handleNotification: async () => ({
       shouldShowAlert: true,
       shouldPlaySound: true,
       shouldSetBadge: true,
     }),
   });
   
   export async function registerForPushNotificationsAsync() {
     let token;
     
     if (Device.isDevice) {
       const { status: existingStatus } = await Notifications.getPermissionsAsync();
       let finalStatus = existingStatus;
       
       if (existingStatus !== 'granted') {
         const { status } = await Notifications.requestPermissionsAsync();
         finalStatus = status;
       }
       
       if (finalStatus !== 'granted') {
         alert('Failed to get push token for push notification!');
         return;
       }
       
       token = (await Notifications.getExpoPushTokenAsync()).data;
       console.log('Push token:', token);
       
       // Send token to backend
       try {
         await usersApi.updateFCMToken(token);
       } catch (error) {
         console.error('Error sending FCM token:', error);
       }
     } else {
       alert('Must use physical device for Push Notifications');
     }
     
     if (Platform.OS === 'android') {
       Notifications.setNotificationChannelAsync('default', {
         name: 'default',
         importance: Notifications.AndroidImportance.MAX,
         vibrationPattern: [0, 250, 250, 250],
         lightColor: '#0066cc',
       });
     }
     
     return token;
   }
   
   export function setupNotificationListeners() {
     // Notification received while app is in foreground
     const notificationListener = Notifications.addNotificationReceivedListener(
       notification => {
         console.log('Notification received:', notification);
       }
     );
     
     // Notification tapped
     const responseListener = Notifications.addNotificationResponseReceivedListener(
       response => {
         console.log('Notification tapped:', response);
         // Handle navigation based on notification data
         const data = response.notification.request.content.data;
         // Navigate to appropriate screen
       }
     );
     
     return () => {
       Notifications.removeNotificationSubscription(notificationListener);
       Notifications.removeNotificationSubscription(responseListener);
     };
   }
   ```

7. ADD TO APP.JS:

   ```javascript
   import { useEffect } from 'react';
   import { registerForPushNotificationsAsync, setupNotificationListeners } from './src/utils/notifications';
   
   export default function App() {
     useEffect(() => {
       registerForPushNotificationsAsync();
       const cleanup = setupNotificationListeners();
       return cleanup;
     }, []);
     
     return (
       <AuthProvider>
         <RootNavigator />
         <StatusBar style="auto" />
       </AuthProvider>
     );
   }
   ```

VERIFICATION CHECKLIST:
- [ ] Can post ride with location
- [ ] Location picker works
- [ ] Google Maps autocomplete works
- [ ] Can select current location
- [ ] Can book ride
- [ ] Stripe card input works
- [ ] Payment processing works
- [ ] Real-time tracking connects
- [ ] Driver location updates
- [ ] Passenger receives updates
- [ ] ETA displays and updates
- [ ] Push notifications received
- [ ] Notifications open correct screen
- [ ] All maps display correctly
- [ ] WebSocket handles disconnect

Please generate React Native app Part 2 with advanced features.
```

---

## TESTING CHECKLIST - SECTION 11

### Post Ride
- [ ] All fields render
- [ ] Location picker opens
- [ ] Can search locations
- [ ] Can select from suggestions
- [ ] Can use current location
- [ ] Map displays selected location
- [ ] Date picker works
- [ ] Time picker works
- [ ] Can set seats (1-7)
- [ ] Can set price
- [ ] Preferences toggles work
- [ ] Can submit form
- [ ] Ride posted successfully

### Booking Flow
- [ ] Can navigate to booking screen
- [ ] Ride details display
- [ ] Can select seats
- [ ] Location pickers work
- [ ] Stripe card field renders
- [ ] Can enter card details
- [ ] Total calculates correctly
- [ ] Can submit booking
- [ ] Payment processed
- [ ] Success message shown

### Maps Integration
- [ ] Maps display correctly
- [ ] Markers show
- [ ] Can search places
- [ ] Autocomplete works
- [ ] Current location works
- [ ] Map responds to touch
- [ ] Route displays

### Real-Time Tracking
Driver:
- [ ] Can start tracking
- [ ] Location permission requested
- [ ] Location sent every 5s
- [ ] Map updates

Passenger:
- [ ] Can view tracking
- [ ] Driver location displays
- [ ] Location updates in real-time
- [ ] ETA displays
- [ ] ETA updates

### Push Notifications
- [ ] Permission requested
- [ ] Token generated
- [ ] Token sent to backend
- [ ] Receives test notification
- [ ] Notification shows alert
- [ ] Tap opens app
- [ ] Navigates to correct screen

### Completion
- [ ] All features working
- [ ] No crashes
- [ ] Ready for Section 12

---

**Date Completed:** _______________
