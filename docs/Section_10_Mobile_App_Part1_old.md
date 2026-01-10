# SJSU RideShare Development Guide
## Section 10: React Native Mobile App - Part 1

**Version:** 1.0  
**Duration:** Week 10  
**Focus:** Mobile app foundation, authentication, navigation, home screen

---

# SECTION 10: React Native Mobile App - Part 1

## Learning Objectives
- Set up React Native with Expo
- Implement authentication flow
- Build navigation structure
- Create reusable components
- Implement API integration
- Handle async storage
- Design responsive UI
- Manage app state with Context API

## Technologies
- React Native (Expo)
- React Navigation
- Axios (API calls)
- AsyncStorage
- Context API (state management)
- Expo Location
- React Native Maps

## Prerequisites
- Sections 1-9 completed ✅
- Node.js installed
- Expo CLI installed
- iOS Simulator or Android Emulator
- Backend APIs running

---

## COMPLETE PROMPT FOR CLAUDE CODE/ANTIGRAVITY

```
PROJECT: SJSU RideShare - React Native Mobile App (Part 1)

CONTEXT:
Sections 1-9 completed. All backend services operational.
Building mobile app with authentication, ride search, and booking features.
Section 10 of 13.

GOAL:
Build mobile app foundation covering:
- Authentication (login, register)
- Navigation structure
- Home screen with ride feed
- Ride search functionality
- Ride details screen
- Profile management

DETAILED REQUIREMENTS:

1. PROJECT SETUP:

   A. Initialize Expo Project:
   ```bash
   npx create-expo-app sjsu-rideshare-mobile
   cd sjsu-rideshare-mobile
   ```
   
   B. Install Dependencies:
   ```bash
   npm install @react-navigation/native
   npm install @react-navigation/native-stack
   npm install @react-navigation/bottom-tabs
   npm install react-native-screens react-native-safe-area-context
   npm install axios
   npm install @react-native-async-storage/async-storage
   npm install react-native-maps
   npm install expo-location
   npm install expo-image-picker
   npm install react-native-elements
   npm install @rneui/themed @rneui/base
   npm install react-native-vector-icons
   npm install date-fns
   ```
   
   C. Configure app.json:
   ```json
   {
     "expo": {
       "name": "SJSU RideShare",
       "slug": "sjsu-rideshare",
       "version": "1.0.0",
       "orientation": "portrait",
       "icon": "./assets/icon.png",
       "userInterfaceStyle": "light",
       "splash": {
         "image": "./assets/splash.png",
         "resizeMode": "contain",
         "backgroundColor": "#0066cc"
       },
       "ios": {
         "supportsTablet": true,
         "bundleIdentifier": "com.sjsu.rideshare"
       },
       "android": {
         "adaptiveIcon": {
           "foregroundImage": "./assets/adaptive-icon.png",
           "backgroundColor": "#0066cc"
         },
         "package": "com.sjsu.rideshare",
         "permissions": [
           "ACCESS_FINE_LOCATION",
           "ACCESS_COARSE_LOCATION"
         ]
       }
     }
   }
   ```

2. PROJECT STRUCTURE:

   ```
   sjsu-rideshare-mobile/
   ├── App.js
   ├── app.json
   ├── src/
   │   ├── api/
   │   │   ├── client.js
   │   │   ├── auth.js
   │   │   ├── rides.js
   │   │   ├── bookings.js
   │   │   └── users.js
   │   ├── components/
   │   │   ├── common/
   │   │   │   ├── Button.js
   │   │   │   ├── Input.js
   │   │   │   ├── Card.js
   │   │   │   └── Loading.js
   │   │   ├── RideCard.js
   │   │   ├── MapView.js
   │   │   ├── UserAvatar.js
   │   │   └── RatingStars.js
   │   ├── screens/
   │   │   ├── auth/
   │   │   │   ├── LoginScreen.js
   │   │   │   ├── RegisterScreen.js
   │   │   │   └── OnboardingScreen.js
   │   │   ├── home/
   │   │   │   ├── HomeScreen.js
   │   │   │   ├── SearchScreen.js
   │   │   │   └── RideDetailsScreen.js
   │   │   ├── rides/
   │   │   │   ├── MyRidesScreen.js
   │   │   │   ├── PostRideScreen.js
   │   │   │   └── RideHistoryScreen.js
   │   │   └── profile/
   │   │       ├── ProfileScreen.js
   │   │       ├── EditProfileScreen.js
   │   │       └── SettingsScreen.js
   │   ├── navigation/
   │   │   ├── AuthNavigator.js
   │   │   ├── MainNavigator.js
   │   │   └── RootNavigator.js
   │   ├── context/
   │   │   ├── AuthContext.js
   │   │   └── RideContext.js
   │   ├── hooks/
   │   │   ├── useAuth.js
   │   │   └── useLocation.js
   │   ├── utils/
   │   │   ├── storage.js
   │   │   ├── validators.js
   │   │   └── formatters.js
   │   ├── constants/
   │   │   ├── colors.js
   │   │   ├── api.js
   │   │   └── theme.js
   │   └── assets/
   │       ├── images/
   │       └── icons/
   ```

3. API CLIENT SETUP (src/api/client.js):

   ```javascript
   import axios from 'axios';
   import AsyncStorage from '@react-native-async-storage/async-storage';
   import { API_BASE_URL } from '../constants/api';
   
   // Create axios instance
   const apiClient = axios.create({
     baseURL: API_BASE_URL,
     timeout: 10000,
     headers: {
       'Content-Type': 'application/json',
     }
   });
   
   // Request interceptor - Add auth token
   apiClient.interceptors.request.use(
     async (config) => {
       try {
         const token = await AsyncStorage.getItem('accessToken');
         if (token) {
           config.headers.Authorization = `Bearer ${token}`;
         }
       } catch (error) {
         console.error('Error getting token:', error);
       }
       return config;
     },
     (error) => {
       return Promise.reject(error);
     }
   );
   
   // Response interceptor - Handle token refresh
   apiClient.interceptors.response.use(
     (response) => response,
     async (error) => {
       const originalRequest = error.config;
       
       // If 401 and haven't retried yet
       if (error.response?.status === 401 && !originalRequest._retry) {
         originalRequest._retry = true;
         
         try {
           // Try to refresh token
           const refreshToken = await AsyncStorage.getItem('refreshToken');
           if (refreshToken) {
             const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
               refresh_token: refreshToken
             });
             
             const { access_token } = response.data;
             await AsyncStorage.setItem('accessToken', access_token);
             
             // Retry original request with new token
             originalRequest.headers.Authorization = `Bearer ${access_token}`;
             return apiClient(originalRequest);
           }
         } catch (refreshError) {
           // Refresh failed, logout user
           await AsyncStorage.multiRemove(['accessToken', 'refreshToken', 'userData']);
           // Navigate to login (handled by AuthContext)
           return Promise.reject(refreshError);
         }
       }
       
       return Promise.reject(error);
     }
   );
   
   export default apiClient;
   ```

4. AUTH CONTEXT (src/context/AuthContext.js):

   ```javascript
   import React, { createContext, useState, useEffect } from 'react';
   import AsyncStorage from '@react-native-async-storage/async-storage';
   import * as authApi from '../api/auth';
   
   export const AuthContext = createContext();
   
   export const AuthProvider = ({ children }) => {
     const [user, setUser] = useState(null);
     const [loading, setLoading] = useState(true);
     const [isAuthenticated, setIsAuthenticated] = useState(false);
     
     // Check if user is logged in on app start
     useEffect(() => {
       checkAuth();
     }, []);
     
     const checkAuth = async () => {
       try {
         const token = await AsyncStorage.getItem('accessToken');
         const userData = await AsyncStorage.getItem('userData');
         
         if (token && userData) {
           setUser(JSON.parse(userData));
           setIsAuthenticated(true);
         }
       } catch (error) {
         console.error('Auth check error:', error);
       } finally {
         setLoading(false);
       }
     };
     
     const login = async (email, password) => {
       try {
         const response = await authApi.login(email, password);
         const { access_token, refresh_token, user } = response.data;
         
         // Store tokens and user data
         await AsyncStorage.multiSet([
           ['accessToken', access_token],
           ['refreshToken', refresh_token],
           ['userData', JSON.stringify(user)]
         ]);
         
         setUser(user);
         setIsAuthenticated(true);
         
         return { success: true };
       } catch (error) {
         return {
           success: false,
           error: error.response?.data?.detail || 'Login failed'
         };
       }
     };
     
     const register = async (userData) => {
       try {
         const response = await authApi.register(userData);
         const { access_token, refresh_token, user } = response.data;
         
         await AsyncStorage.multiSet([
           ['accessToken', access_token],
           ['refreshToken', refresh_token],
           ['userData', JSON.stringify(user)]
         ]);
         
         setUser(user);
         setIsAuthenticated(true);
         
         return { success: true };
       } catch (error) {
         return {
           success: false,
           error: error.response?.data?.detail || 'Registration failed'
         };
       }
     };
     
     const logout = async () => {
       try {
         await AsyncStorage.multiRemove(['accessToken', 'refreshToken', 'userData']);
         setUser(null);
         setIsAuthenticated(false);
       } catch (error) {
         console.error('Logout error:', error);
       }
     };
     
     const updateUser = async (updatedData) => {
       try {
         const newUserData = { ...user, ...updatedData };
         await AsyncStorage.setItem('userData', JSON.stringify(newUserData));
         setUser(newUserData);
       } catch (error) {
         console.error('Update user error:', error);
       }
     };
     
     return (
       <AuthContext.Provider
         value={{
           user,
           isAuthenticated,
           loading,
           login,
           register,
           logout,
           updateUser
         }}
       >
         {children}
       </AuthContext.Provider>
     );
   };
   ```

5. LOGIN SCREEN (src/screens/auth/LoginScreen.js):

   ```javascript
   import React, { useState } from 'react';
   import {
     View,
     Text,
     TextInput,
     TouchableOpacity,
     StyleSheet,
     KeyboardAvoidingView,
     Platform,
     Alert
   } from 'react-native';
   import { useAuth } from '../../hooks/useAuth';
   import { COLORS } from '../../constants/colors';
   import Button from '../../components/common/Button';
   import Input from '../../components/common/Input';
   
   export default function LoginScreen({ navigation }) {
     const { login } = useAuth();
     const [email, setEmail] = useState('');
     const [password, setPassword] = useState('');
     const [loading, setLoading] = useState(false);
     const [errors, setErrors] = useState({});
     
     const validateForm = () => {
       const newErrors = {};
       
       // Email validation
       if (!email) {
         newErrors.email = 'Email is required';
       } else if (!email.endsWith('@sjsu.edu')) {
         newErrors.email = 'Must use SJSU email (@sjsu.edu)';
       }
       
       // Password validation
       if (!password) {
         newErrors.password = 'Password is required';
       } else if (password.length < 8) {
         newErrors.password = 'Password must be at least 8 characters';
       }
       
       setErrors(newErrors);
       return Object.keys(newErrors).length === 0;
     };
     
     const handleLogin = async () => {
       if (!validateForm()) return;
       
       setLoading(true);
       const result = await login(email, password);
       setLoading(false);
       
       if (!result.success) {
         Alert.alert('Login Failed', result.error);
       }
       // Navigation handled by RootNavigator when isAuthenticated changes
     };
     
     return (
       <KeyboardAvoidingView
         style={styles.container}
         behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
       >
         <View style={styles.content}>
           <Text style={styles.title}>SJSU RideShare</Text>
           <Text style={styles.subtitle}>Safe carpooling for students</Text>
           
           <Input
             placeholder="Email (@sjsu.edu)"
             value={email}
             onChangeText={setEmail}
             keyboardType="email-address"
             autoCapitalize="none"
             error={errors.email}
             leftIcon="email"
           />
           
           <Input
             placeholder="Password"
             value={password}
             onChangeText={setPassword}
             secureTextEntry
             error={errors.password}
             leftIcon="lock"
           />
           
           <TouchableOpacity onPress={() => navigation.navigate('ForgotPassword')}>
             <Text style={styles.forgotText}>Forgot Password?</Text>
           </TouchableOpacity>
           
           <Button
             title="Login"
             onPress={handleLogin}
             loading={loading}
             style={styles.loginButton}
           />
           
           <View style={styles.registerContainer}>
             <Text style={styles.registerText}>Don't have an account? </Text>
             <TouchableOpacity onPress={() => navigation.navigate('Register')}>
               <Text style={styles.registerLink}>Sign Up</Text>
             </TouchableOpacity>
           </View>
         </View>
       </KeyboardAvoidingView>
     );
   }
   
   const styles = StyleSheet.create({
     container: {
       flex: 1,
       backgroundColor: COLORS.white,
     },
     content: {
       flex: 1,
       padding: 20,
       justifyContent: 'center',
     },
     title: {
       fontSize: 32,
       fontWeight: 'bold',
       color: COLORS.primary,
       textAlign: 'center',
       marginBottom: 8,
     },
     subtitle: {
       fontSize: 16,
       color: COLORS.gray,
       textAlign: 'center',
       marginBottom: 40,
     },
     forgotText: {
       color: COLORS.primary,
       textAlign: 'right',
       marginTop: 8,
       marginBottom: 24,
     },
     loginButton: {
       marginTop: 16,
     },
     registerContainer: {
       flexDirection: 'row',
       justifyContent: 'center',
       marginTop: 24,
     },
     registerText: {
       color: COLORS.gray,
     },
     registerLink: {
       color: COLORS.primary,
       fontWeight: 'bold',
     },
   });
   ```

6. REGISTER SCREEN (src/screens/auth/RegisterScreen.js):

   ```javascript
   import React, { useState } from 'react';
   import {
     View,
     Text,
     ScrollView,
     StyleSheet,
     Alert
   } from 'react-native';
   import { useAuth } from '../../hooks/useAuth';
   import Input from '../../components/common/Input';
   import Button from '../../components/common/Button';
   import { COLORS } from '../../constants/colors';
   
   export default function RegisterScreen({ navigation }) {
     const { register } = useAuth();
     const [formData, setFormData] = useState({
       email: '',
       password: '',
       confirmPassword: '',
       firstName: '',
       lastName: '',
       phone: ''
     });
     const [loading, setLoading] = useState(false);
     const [errors, setErrors] = useState({});
     
     const updateField = (field, value) => {
       setFormData(prev => ({ ...prev, [field]: value }));
       // Clear error when user starts typing
       if (errors[field]) {
         setErrors(prev => ({ ...prev, [field]: null }));
       }
     };
     
     const validateForm = () => {
       const newErrors = {};
       
       // Email
       if (!formData.email.endsWith('@sjsu.edu')) {
         newErrors.email = 'Must use SJSU email';
       }
       
       // Password
       if (formData.password.length < 8) {
         newErrors.password = 'At least 8 characters';
       }
       if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
         newErrors.password = 'Must include uppercase, lowercase, and number';
       }
       
       // Confirm password
       if (formData.password !== formData.confirmPassword) {
         newErrors.confirmPassword = 'Passwords do not match';
       }
       
       // Name
       if (!formData.firstName.trim()) {
         newErrors.firstName = 'First name required';
       }
       if (!formData.lastName.trim()) {
         newErrors.lastName = 'Last name required';
       }
       
       // Phone
       if (!/^\d{10}$/.test(formData.phone.replace(/\D/g, ''))) {
         newErrors.phone = 'Invalid phone number';
       }
       
       setErrors(newErrors);
       return Object.keys(newErrors).length === 0;
     };
     
     const handleRegister = async () => {
       if (!validateForm()) return;
       
       setLoading(true);
       const result = await register({
         email: formData.email,
         password: formData.password,
         first_name: formData.firstName,
         last_name: formData.lastName,
         phone: formData.phone
       });
       setLoading(false);
       
       if (!result.success) {
         Alert.alert('Registration Failed', result.error);
       }
     };
     
     return (
       <ScrollView style={styles.container}>
         <View style={styles.content}>
           <Text style={styles.title}>Create Account</Text>
           
           <Input
             placeholder="First Name"
             value={formData.firstName}
             onChangeText={(val) => updateField('firstName', val)}
             error={errors.firstName}
             leftIcon="person"
           />
           
           <Input
             placeholder="Last Name"
             value={formData.lastName}
             onChangeText={(val) => updateField('lastName', val)}
             error={errors.lastName}
             leftIcon="person"
           />
           
           <Input
             placeholder="Email (@sjsu.edu)"
             value={formData.email}
             onChangeText={(val) => updateField('email', val)}
             keyboardType="email-address"
             autoCapitalize="none"
             error={errors.email}
             leftIcon="email"
           />
           
           <Input
             placeholder="Phone"
             value={formData.phone}
             onChangeText={(val) => updateField('phone', val)}
             keyboardType="phone-pad"
             error={errors.phone}
             leftIcon="phone"
           />
           
           <Input
             placeholder="Password"
             value={formData.password}
             onChangeText={(val) => updateField('password', val)}
             secureTextEntry
             error={errors.password}
             leftIcon="lock"
           />
           
           <Input
             placeholder="Confirm Password"
             value={formData.confirmPassword}
             onChangeText={(val) => updateField('confirmPassword', val)}
             secureTextEntry
             error={errors.confirmPassword}
             leftIcon="lock"
           />
           
           <Button
             title="Sign Up"
             onPress={handleRegister}
             loading={loading}
             style={styles.button}
           />
           
           <Button
             title="Already have an account? Login"
             onPress={() => navigation.navigate('Login')}
             variant="outline"
             style={styles.button}
           />
         </View>
       </ScrollView>
     );
   }
   
   const styles = StyleSheet.create({
     container: {
       flex: 1,
       backgroundColor: COLORS.white,
     },
     content: {
       padding: 20,
     },
     title: {
       fontSize: 28,
       fontWeight: 'bold',
       color: COLORS.primary,
       marginBottom: 24,
     },
     button: {
       marginTop: 16,
     },
   });
   ```

7. HOME SCREEN (src/screens/home/HomeScreen.js):

   ```javascript
   import React, { useState, useEffect } from 'react';
   import {
     View,
     Text,
     FlatList,
     RefreshControl,
     StyleSheet,
     TouchableOpacity
   } from 'react-native';
   import { useAuth } from '../../hooks/useAuth';
   import * as ridesApi from '../../api/rides';
   import RideCard from '../../components/RideCard';
   import Button from '../../components/common/Button';
   import { COLORS } from '../../constants/colors';
   
   export default function HomeScreen({ navigation }) {
     const { user } = useAuth();
     const [rides, setRides] = useState([]);
     const [loading, setLoading] = useState(false);
     const [refreshing, setRefreshing] = useState(false);
     
     useEffect(() => {
       loadRides();
     }, []);
     
     const loadRides = async () => {
       setLoading(true);
       try {
         const response = await ridesApi.getAvailableRides();
         setRides(response.data);
       } catch (error) {
         console.error('Error loading rides:', error);
       } finally {
         setLoading(false);
       }
     };
     
     const onRefresh = async () => {
       setRefreshing(true);
       await loadRides();
       setRefreshing(false);
     };
     
     const renderHeader = () => (
       <View style={styles.header}>
         <Text style={styles.greeting}>Hi, {user?.first_name}!</Text>
         <Text style={styles.subtitle}>Where would you like to go?</Text>
         
         <TouchableOpacity
           style={styles.searchBar}
           onPress={() => navigation.navigate('Search')}
         >
           <Text style={styles.searchPlaceholder}>Search for rides...</Text>
         </TouchableOpacity>
         
         <View style={styles.quickActions}>
           <Button
             title="Post a Ride"
             onPress={() => navigation.navigate('PostRide')}
             style={styles.actionButton}
           />
           <Button
             title="My Bookings"
             onPress={() => navigation.navigate('MyRides')}
             variant="outline"
             style={styles.actionButton}
           />
         </View>
         
         <Text style={styles.sectionTitle}>Available Rides</Text>
       </View>
     );
     
     return (
       <View style={styles.container}>
         <FlatList
           data={rides}
           renderItem={({ item }) => (
             <RideCard
               ride={item}
               onPress={() => navigation.navigate('RideDetails', { rideId: item.id })}
             />
           )}
           keyExtractor={(item) => item.id}
           ListHeaderComponent={renderHeader}
           refreshControl={
             <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
           }
           contentContainerStyle={styles.list}
         />
       </View>
     );
   }
   
   const styles = StyleSheet.create({
     container: {
       flex: 1,
       backgroundColor: COLORS.background,
     },
     header: {
       padding: 20,
       backgroundColor: COLORS.white,
     },
     greeting: {
       fontSize: 24,
       fontWeight: 'bold',
       color: COLORS.text,
     },
     subtitle: {
       fontSize: 16,
       color: COLORS.gray,
       marginTop: 4,
       marginBottom: 20,
     },
     searchBar: {
       backgroundColor: COLORS.lightGray,
       padding: 16,
       borderRadius: 8,
       marginBottom: 20,
     },
     searchPlaceholder: {
       color: COLORS.gray,
     },
     quickActions: {
       flexDirection: 'row',
       justifyContent: 'space-between',
       marginBottom: 24,
     },
     actionButton: {
       flex: 1,
       marginHorizontal: 4,
     },
     sectionTitle: {
       fontSize: 18,
       fontWeight: '600',
       color: COLORS.text,
       marginBottom: 8,
     },
     list: {
       paddingBottom: 20,
     },
   });
   ```

8. RIDE CARD COMPONENT (src/components/RideCard.js):

   ```javascript
   import React from 'react';
   import { View, Text, TouchableOpacity, StyleSheet, Image } from 'react-native';
   import { format } from 'date-fns';
   import RatingStars from './RatingStars';
   import { COLORS } from '../constants/colors';
   
   export default function RideCard({ ride, onPress }) {
     return (
       <TouchableOpacity style={styles.card} onPress={onPress}>
         <View style={styles.header}>
           <View style={styles.driverInfo}>
             <Image
               source={{ uri: ride.driver_info?.profile_photo || 'default-avatar-url' }}
               style={styles.avatar}
             />
             <View>
               <Text style={styles.driverName}>
                 {ride.driver_info?.first_name} {ride.driver_info?.last_name}
               </Text>
               <RatingStars rating={ride.driver_info?.rating || 0} size={14} />
             </View>
           </View>
           <View style={styles.priceContainer}>
             <Text style={styles.price}>${ride.price_per_seat}</Text>
             <Text style={styles.perSeat}>per seat</Text>
           </View>
         </View>
         
         <View style={styles.routeContainer}>
           <View style={styles.routeLine}>
             <View style={styles.dot} />
             <View style={styles.line} />
             <View style={[styles.dot, styles.destinationDot]} />
           </View>
           <View style={styles.addresses}>
             <Text style={styles.address} numberOfLines={1}>
               {ride.origin.address}
             </Text>
             <Text style={[styles.address, styles.destination]} numberOfLines={1}>
               {ride.destination.address}
             </Text>
           </View>
         </View>
         
         <View style={styles.footer}>
           <Text style={styles.time}>
             {format(new Date(ride.departure_time), 'MMM d, h:mm a')}
           </Text>
           <Text style={styles.seats}>
             {ride.available_seats} {ride.available_seats === 1 ? 'seat' : 'seats'} left
           </Text>
         </View>
       </TouchableOpacity>
     );
   }
   
   const styles = StyleSheet.create({
     card: {
       backgroundColor: COLORS.white,
       borderRadius: 12,
       padding: 16,
       marginHorizontal: 16,
       marginVertical: 8,
       shadowColor: '#000',
       shadowOffset: { width: 0, height: 2 },
       shadowOpacity: 0.1,
       shadowRadius: 4,
       elevation: 3,
     },
     header: {
       flexDirection: 'row',
       justifyContent: 'space-between',
       marginBottom: 16,
     },
     driverInfo: {
       flexDirection: 'row',
       alignItems: 'center',
     },
     avatar: {
       width: 40,
       height: 40,
       borderRadius: 20,
       marginRight: 12,
     },
     driverName: {
       fontSize: 16,
       fontWeight: '600',
       color: COLORS.text,
       marginBottom: 4,
     },
     priceContainer: {
       alignItems: 'flex-end',
     },
     price: {
       fontSize: 24,
       fontWeight: 'bold',
       color: COLORS.primary,
     },
     perSeat: {
       fontSize: 12,
       color: COLORS.gray,
     },
     routeContainer: {
       flexDirection: 'row',
       marginBottom: 16,
     },
     routeLine: {
       width: 20,
       alignItems: 'center',
       marginRight: 12,
     },
     dot: {
       width: 8,
       height: 8,
       borderRadius: 4,
       backgroundColor: COLORS.primary,
     },
     line: {
       width: 2,
       flex: 1,
       backgroundColor: COLORS.lightGray,
       marginVertical: 4,
     },
     destinationDot: {
       backgroundColor: COLORS.success,
     },
     addresses: {
       flex: 1,
       justifyContent: 'space-between',
     },
     address: {
       fontSize: 14,
       color: COLORS.text,
     },
     destination: {
       marginTop: 8,
     },
     footer: {
       flexDirection: 'row',
       justifyContent: 'space-between',
       paddingTop: 12,
       borderTopWidth: 1,
       borderTopColor: COLORS.lightGray,
     },
     time: {
       fontSize: 14,
       color: COLORS.gray,
     },
     seats: {
       fontSize: 14,
       fontWeight: '600',
       color: COLORS.primary,
     },
   });
   ```

9. NAVIGATION SETUP (src/navigation/RootNavigator.js):

   ```javascript
   import React from 'react';
   import { NavigationContainer } from '@react-navigation/native';
   import { useAuth } from '../hooks/useAuth';
   import AuthNavigator from './AuthNavigator';
   import MainNavigator from './MainNavigator';
   import Loading from '../components/common/Loading';
   
   export default function RootNavigator() {
     const { isAuthenticated, loading } = useAuth();
     
     if (loading) {
       return <Loading />;
     }
     
     return (
       <NavigationContainer>
         {isAuthenticated ? <MainNavigator /> : <AuthNavigator />}
       </NavigationContainer>
     );
   }
   ```

10. CONSTANTS (src/constants/colors.js & api.js):

    colors.js:
    ```javascript
    export const COLORS = {
      primary: '#0066cc',
      secondary: '#00cc66',
      success: '#28a745',
      danger: '#dc3545',
      warning: '#ffc107',
      info: '#17a2b8',
      
      white: '#ffffff',
      black: '#000000',
      text: '#212529',
      gray: '#6c757d',
      lightGray: '#f8f9fa',
      background: '#f5f5f5',
      
      border: '#dee2e6',
      placeholder: '#adb5bd',
    };
    ```
    
    api.js:
    ```javascript
    // Update with your backend URL
    export const API_BASE_URL = __DEV__
      ? 'http://localhost:8000/api/v1'  // Development
      : 'https://api.sjsurideshare.com/api/v1';  // Production
    ```

11. APP.JS:

    ```javascript
    import React from 'react';
    import { StatusBar } from 'expo-status-bar';
    import { AuthProvider } from './src/context/AuthContext';
    import RootNavigator from './src/navigation/RootNavigator';
    
    export default function App() {
      return (
        <AuthProvider>
          <RootNavigator />
          <StatusBar style="auto" />
        </AuthProvider>
      );
    }
    ```

12. TESTING:

    Manual Testing Checklist:
    - Test on iOS Simulator
    - Test on Android Emulator
    - Test on physical device
    - Test all user flows
    - Test offline behavior
    - Test token refresh
    - Test form validations

VERIFICATION CHECKLIST:
- [ ] App runs on iOS
- [ ] App runs on Android
- [ ] Can register new user
- [ ] Email validation works (@sjsu.edu)
- [ ] Password validation works
- [ ] Can login
- [ ] Token stored in AsyncStorage
- [ ] Auto-login on app restart
- [ ] Home screen loads
- [ ] Ride feed displays
- [ ] Can navigate to ride details
- [ ] Can refresh ride list
- [ ] API calls successful
- [ ] Token refresh works on 401
- [ ] Can logout
- [ ] UI responsive
- [ ] No console errors

Please generate React Native mobile app foundation with authentication.
```

---

## TESTING CHECKLIST - SECTION 10

### Setup
- [ ] Expo installed
- [ ] Project created
- [ ] Dependencies installed
- [ ] iOS Simulator working
- [ ] Android Emulator working

### Authentication
Register:
- [ ] Can navigate to register screen
- [ ] All fields render
- [ ] Email validation works
- [ ] Password strength indicator works
- [ ] Phone validation works
- [ ] Can submit form
- [ ] Success navigates to home
- [ ] Error shows alert

Login:
- [ ] Can navigate to login screen
- [ ] Email input works
- [ ] Password input works
- [ ] Forgot password link works
- [ ] Can submit
- [ ] Success navigates to home
- [ ] Error shows message
- [ ] Token stored

### Home Screen
- [ ] Loads after login
- [ ] Shows greeting with name
- [ ] Search bar visible
- [ ] Quick action buttons work
- [ ] Ride feed loads
- [ ] Rides display correctly
- [ ] Pull to refresh works
- [ ] Can tap ride card

### Ride Card
- [ ] Driver info displays
- [ ] Rating shows
- [ ] Price displays
- [ ] Route shows correctly
- [ ] Departure time formatted
- [ ] Available seats shown
- [ ] Tap navigates to details

### Navigation
- [ ] Tab navigation works
- [ ] Stack navigation works
- [ ] Back button works
- [ ] Deep linking works (optional)

### API Integration
- [ ] Can connect to backend
- [ ] Login API call works
- [ ] Register API call works
- [ ] Get rides API call works
- [ ] Auth token sent in headers
- [ ] 401 triggers token refresh
- [ ] Refresh token works

### Storage
- [ ] Tokens saved to AsyncStorage
- [ ] User data saved
- [ ] Data persists on app restart
- [ ] Logout clears storage

### UI/UX
- [ ] Responsive on different screens
- [ ] Keyboard handling works
- [ ] Loading states show
- [ ] Error states show
- [ ] Empty states show
- [ ] Icons display correctly

### Completion
- [ ] All tests passing
- [ ] No console errors
- [ ] No warnings
- [ ] Ready for Section 11

---

**Date Completed:** _______________  
**Device Tested:** _______________  
**Notes:** _______________
