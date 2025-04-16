
-- users table
CREATE TABLE users (
    UserID SERIAL PRIMARY KEY,
    ID VARCHAR(255),
    password VARCHAR(255),
    birthyear VARCHAR(4),
    region VARCHAR(50),
    gender VARCHAR(10),
    signup_date DATE,
    last_activity DATE,
    role VARCHAR(20)
);

-- sessions table
CREATE TABLE sessions (
    sessionID SERIAL PRIMARY KEY,
    UserID INT REFERENCES users(UserID),
    login_time TIMESTAMP,
    logout_time TIMESTAMP,
    status VARCHAR(20)
);

-- chat_log table
CREATE TABLE chat_log (
    chat_ID SERIAL PRIMARY KEY,
    UserID INT REFERENCES users(UserID),
    chat_time TIMESTAMP,
    utterance VARCHAR(20),
    chat_content TEXT
);

-- main_categories table
CREATE TABLE main_categories (
    main_category_ID SERIAL PRIMARY KEY,
    main_category VARCHAR(50)
);

-- middle_categories table
CREATE TABLE middle_categories (
    middle_category_ID SERIAL PRIMARY KEY,
    middle_category VARCHAR(50)
);

-- sub_categories table
CREATE TABLE sub_categories (
    sub_category_ID SERIAL PRIMARY KEY,
    sub_category VARCHAR(50)
);

-- main_category_mapping table
CREATE TABLE main_category_mapping (
    main_category_mapping_ID SERIAL PRIMARY KEY,
    main_category_probability NUMERIC
);

-- middle_category_mapping table
CREATE TABLE middle_category_mapping (
    middle_category_mapping_ID SERIAL PRIMARY KEY,
    middle_category_probability NUMERIC
);

-- sub_category_mapping table
CREATE TABLE sub_category_mapping (
    sub_category_mapping_ID SERIAL PRIMARY KEY,
    sub_category_probability NUMERIC
);

-- emotions table
CREATE TABLE emotions (
    emotion_ID SERIAL PRIMARY KEY,
    chat_ID INT REFERENCES chat_log(chat_ID),
    main_category_ID INT REFERENCES main_categories(main_category_ID),
    middle_category_ID INT REFERENCES middle_categories(middle_category_ID),
    sub_category_ID INT REFERENCES sub_categories(sub_category_ID),
    main_category_mapping_ID INT REFERENCES main_category_mapping(main_category_mapping_ID),
    middle_category_mapping_ID INT REFERENCES middle_category_mapping(middle_category_mapping_ID),
    sub_category_mapping_ID INT REFERENCES sub_category_mapping(sub_category_mapping_ID),
    sentence TEXT,
    analysis_date DATE,
    emotion_score NUMERIC
);

-- AlertType table
CREATE TABLE AlertType (
    alert_type_ID SERIAL PRIMARY KEY,
    alert_type VARCHAR(50),
    severity_level VARCHAR(20),
    description VARCHAR(255)
);

-- emotion_change_alerts table
CREATE TABLE emotion_change_alerts (
    alert_ID SERIAL PRIMARY KEY,
    UserID INT REFERENCES users(UserID),
    emotion_ID INT REFERENCES emotions(emotion_ID),
    alert_type_ID INT REFERENCES AlertType(alert_type_ID),
    duration NUMERIC,
    alert_message VARCHAR(255),
    alert_time TIMESTAMP,
    alert_status VARCHAR(20)
);

-- emotion_based_recommendations table
CREATE TABLE emotion_based_recommendations (
    recommendation_ID CHAR(18) PRIMARY KEY,
    UserID INT REFERENCES users(UserID),
    emotion CHAR(18),
    recommended_item CHAR(18),
    recommendation_type CHAR(18),
    recommendation_time CHAR(18)
);

-- API_logs table
CREATE TABLE API_logs (
    API_ID SERIAL PRIMARY KEY,
    UserID INT REFERENCES users(UserID),
    API_name VARCHAR(50),
    call_time TIMESTAMP,
    response_status VARCHAR(20),
    response_content TEXT
);
