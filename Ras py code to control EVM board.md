不需要額外寫一個write的低階code了
`self.bus.write_byte_data(self.i2c_address, reg, data)`
`data = bus.read_byte_data(LMP91000_I2C_ADDRESS, register)`

```python
# mimic requestFrom()
self.bus.write_byte(LMP91000_I2C_ADDRESS, reg)
data = self.bus.read_byte(LMP91000_I2C_ADDRESS)
```

這樣鎖定是必要的嗎，
`self.lock()`

考慮整合`setBiasSign`
SDA, SCL根本不用設定腳位

確認ADC轉換出來的單位是V嗎


