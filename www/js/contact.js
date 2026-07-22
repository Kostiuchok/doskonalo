/*--------------------------------------------------
Function Contact Formular
---------------------------------------------------*/	
		
	function ContactForm() {

		if( $('#contact-formular').length > 0 ){

			var DIRECTUS = 'https://admin.doskonalo.clinic';

			var PHONE_RE = /^[0-9+\s()-]{7,20}$/;
			var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

			$('#contactform').off('submit').on('submit', function(e) {
				e.preventDefault();
				var name = $('#name').val().trim();
				var phone = $('#phone').val().trim();
				var email = $('#email').val().trim();
				var contactMethod = $('#browsers').val();

				if ($('#website').val()) {
					// honeypot field filled in — silently drop, likely a bot
					return;
				}
				if (!name) {
					$('#message').html('<div class="error_message">Будь ласка, вкажіть ваше ім\'я.</div>').slideDown('slow');
					return;
				}
				if (!phone && !email) {
					$('#message').html('<div class="error_message">Будь ласка, вкажіть телефон або email.</div>').slideDown('slow');
					return;
				}
				if (phone && !PHONE_RE.test(phone)) {
					$('#message').html('<div class="error_message">Будь ласка, вкажіть коректний номер телефону.</div>').slideDown('slow');
					return;
				}
				if (email && !EMAIL_RE.test(email)) {
					$('#message').html('<div class="error_message">Будь ласка, вкажіть коректний email.</div>').slideDown('slow');
					return;
				}

				$('#submit').addClass('is-disabled');
				$('#message').slideUp(300);

				fetch(DIRECTUS + '/items/contact_submissions', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						name: name,
						phone: phone,
						email: email,
						message: 'Зручний спосіб зв\'язку: ' + contactMethod
					})
				})
				.then(function(r) {
					if (!r.ok) throw new Error('HTTP ' + r.status);
				})
				.then(function() {
					$('#contactform').slideUp('slow');
					$('#message').html('<div id="success_page"><h3>Дякуємо!</h3><p style="color:#000;">Ми зв\'яжемося з вами найближчим часом.</p></div>').slideDown('slow');
				})
				.catch(function() {
					$('#submit').removeClass('is-disabled');
					$('#message').html('<div class="error_message">Сталася помилка. Будь ласка, зателефонуйте нам: <a href="tel:+380980320012">+380 (98) 032 0012</a></div>').slideDown('slow');
				});
			});

			$('#submit').off('click').on('click', function(e) {
				e.preventDefault();
				$('#contactform').trigger('submit');
			});
		}


	}//End ContactForm


/*--------------------------------------------------
Function Contact Map
---------------------------------------------------*/	
		
	function ContactMap() {	
	
		if( jQuery('#map_canvas').length > 0 ){					
			var latlng = new google.maps.LatLng(43.270441,6.640888);
			var settings = {
				zoom: 15,
				disableDefaultUI: true,
				center: new google.maps.LatLng(43.270441,6.640888),
				mapTypeControl: false,
				scrollwheel: false,
				draggable: true,
				panControl:false,
				scaleControl: false,
				zoomControl: false,
				streetViewControl:false,
				navigationControl: false};			
				var newstyle = [
				{
					"featureType": "all",
					"elementType": "labels.text.fill",
					"stylers": [
						{
							"saturation": 36
						},
						{
							"color": "#000000"
						},
						{
							"lightness": 40
						}
					]
				},
				{
					"featureType": "all",
					"elementType": "labels.text.stroke",
					"stylers": [
						{
							"visibility": "on"
						},
						{
							"color": "#000000"
						},
						{
							"lightness": 16
						}
					]
				},
				{
					"featureType": "all",
					"elementType": "labels.icon",
					"stylers": [
						{
							"visibility": "off"
						}
					]
				},
				{
					"featureType": "administrative",
					"elementType": "geometry.fill",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 20
						}
					]
				},
				{
					"featureType": "administrative",
					"elementType": "geometry.stroke",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 17
						},
						{
							"weight": 1.2
						}
					]
				},
				{
					"featureType": "landscape",
					"elementType": "geometry",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 20
						}
					]
				},
				{
					"featureType": "poi",
					"elementType": "geometry",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 21
						}
					]
				},
				{
					"featureType": "road.highway",
					"elementType": "geometry.fill",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 17
						}
					]
				},
				{
					"featureType": "road.highway",
					"elementType": "geometry.stroke",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 29
						},
						{
							"weight": 0.2
						}
					]
				},
				{
					"featureType": "road.arterial",
					"elementType": "geometry",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 18
						}
					]
				},
				{
					"featureType": "road.local",
					"elementType": "geometry",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 16
						}
					]
				},
				{
					"featureType": "transit",
					"elementType": "geometry",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 19
						}
					]
				},
				{
					"featureType": "water",
					"elementType": "geometry",
					"stylers": [
						{
							"color": "#000000"
						},
						{
							"lightness": 17
						}
					]
				}
			];
			var mapOptions = {
				styles: newstyle,
				mapTypeControlOptions: {
					 mapTypeIds: [google.maps.MapTypeId.ROADMAP, 'holver']
				}
			};
			var map = new google.maps.Map(document.getElementById("map_canvas"), settings);	
			var mapType = new google.maps.StyledMapType(newstyle, { name:"Grayscale" });    
				map.mapTypes.set('holver', mapType);
				map.setMapTypeId('holver');
						
			
			google.maps.event.addDomListener(window, "resize", function() {
				var center = map.getCenter();
				google.maps.event.trigger(map, "resize");
				map.setCenter(center);
			});	
			var contentString = '<div id="content-map-marker" style="text-align:center; padding-top:10px; padding-left:10px">'+
				'<div id="siteNotice">'+
				'</div>'+
				'<h4 id="firstHeading" class="firstHeading" style="color:#000!important; font-weight:600; margin-bottom:0px;">Hello Friend!</h4>'+
				'<div id="bodyContent">'+
				'<p color:#999; font-size:14px; margin-bottom:10px">Here we are. Come to drink a coffee!</p>'+
				'</div>'+
				'</div>';
			var infowindow = new google.maps.InfoWindow({
				content: contentString
			});	
			var companyImage = new google.maps.MarkerImage('images/marker.png',
				new google.maps.Size(58,63),<!-- Width and height of the marker -->
				new google.maps.Point(0,0),
				new google.maps.Point(35,20)<!-- Position of the marker -->
			);
			var companyPos = new google.maps.LatLng(43.270441,6.640888);	
			var companyMarker = new google.maps.Marker({
				position: companyPos,
				map: map,
				icon: companyImage,               
				title:"Our Office",
				zIndex: 3});	
			google.maps.event.addListener(companyMarker, 'click', function() {
				infowindow.open(map,companyMarker);
			});	
		}
		
		return false
	
	}//End ContactMap